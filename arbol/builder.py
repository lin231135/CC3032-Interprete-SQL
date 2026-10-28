"""
ASTBuilder: Visitor de ANTLR que transforma el arbol sintactico (ParseTree)
en el AST de arbol/nodes.py.

Normaliza los identificadores a minusculas, quita las comillas de los
literales, pliega `-<numero>` en un literal negativo y `NOT EXISTS` en
Exists(negado=True). Los errores que ya se detectan aqui (fecha literal
invalida, VARCHAR(0)) se reportan como errores semanticos.
"""

from __future__ import annotations

from core.errors import ErrorReporter
from core.types import BOOLEAN, DATE, FLOAT, INT, NULO, VARCHAR, TipoSQL, parsear_fecha
from generated.SQLParser import SQLParser
from generated.SQLVisitor import SQLVisitor

from arbol import nodes as n


def _texto(ctx) -> str:
    """Texto ORIGINAL (con espacios) que cubre el contexto."""
    if ctx.start is None or ctx.stop is None or ctx.stop.stop < ctx.start.start:
        return ctx.getText()
    return ctx.start.getInputStream().getText(ctx.start.start, ctx.stop.stop)


def _pos(ctx) -> dict:
    token = ctx.start if hasattr(ctx, "start") else ctx.symbol
    return {"linea": token.line, "columna": token.column + 1}


class ASTBuilder(SQLVisitor):
    def __init__(self) -> None:
        self.reporter = ErrorReporter()

    # ------------------------------------------------------------------
    # script / sentencias
    # ------------------------------------------------------------------

    def visitScript(self, ctx: SQLParser.ScriptContext) -> n.Script:
        sentencias = [self.visit(s) for s in ctx.statement()]
        return n.Script(sentencias, **_pos(ctx))

    def visitStatement(self, ctx: SQLParser.StatementContext):
        sentencia = self.visit(ctx.getChild(0))
        sentencia.texto = _texto(ctx)
        return sentencia

    def _id(self, ctx: SQLParser.IdentifierContext) -> str:
        return ctx.getText().lower()

    # --- DDL -------------------------------------------------------------

    def visitCreateTable(self, ctx: SQLParser.CreateTableContext) -> n.CreateTable:
        columnas: list[n.ColumnDef] = []
        pk: list[str] = []
        uniques: list[list[str]] = []
        foraneas: list[n.ForeignKey] = []
        for elem in ctx.tableElement():
            if elem.columnDef() is not None:
                col = self.visit(elem.columnDef())
                columnas.append(col)
                if col.referencia is not None:
                    foraneas.append(n.ForeignKey(col.nombre, *col.referencia, **_pos(elem)))
                continue
            restr = elem.tableConstraint()
            if isinstance(restr, SQLParser.TablePkContext):
                if pk:
                    self.reporter.error(n.Nodo(**_pos(restr)), "tabla", "La tabla tiene más de una PRIMARY KEY")
                pk = self._lista_ids(restr.identifierList())
            elif isinstance(restr, SQLParser.TableUniqueContext):
                uniques.append(self._lista_ids(restr.identifierList()))
            else:
                ids = restr.identifier()
                foraneas.append(n.ForeignKey(self._id(ids[0]), self._id(ids[1]), self._id(ids[2]), **_pos(restr)))
        return n.CreateTable(self._id(ctx.identifier()), columnas, pk, uniques, foraneas,
                             si_no_existe=ctx.IF() is not None, **_pos(ctx))

    def _lista_ids(self, ctx: SQLParser.IdentifierListContext) -> list[str]:
        return [self._id(i) for i in ctx.identifier()]

    def visitColumnDef(self, ctx: SQLParser.ColumnDefContext) -> n.ColumnDef:
        col = n.ColumnDef(self._id(ctx.identifier()), self.visit(ctx.dataType()), **_pos(ctx))
        for restr in ctx.columnConstraint():
            if isinstance(restr, SQLParser.PkConstraintContext):
                col.primary_key = True
                col.not_null = True
            elif isinstance(restr, SQLParser.NotNullConstraintContext):
                col.not_null = True
            elif isinstance(restr, SQLParser.UniqueConstraintContext):
                col.unique = True
            elif isinstance(restr, SQLParser.DefaultConstraintContext):
                col.default = self.visit(restr.signedLiteral())
            elif isinstance(restr, SQLParser.ReferencesConstraintContext):
                ids = restr.identifier()
                col.referencia = (self._id(ids[0]), self._id(ids[1]))
        return col

    def visitIntType(self, ctx) -> TipoSQL:
        return INT

    def visitFloatType(self, ctx) -> TipoSQL:
        return FLOAT

    def visitBooleanType(self, ctx) -> TipoSQL:
        return BOOLEAN

    def visitDateType(self, ctx) -> TipoSQL:
        return DATE

    def visitVarcharType(self, ctx: SQLParser.VarcharTypeContext) -> TipoSQL:
        longitud = int(ctx.INT_LIT().getText())
        if longitud <= 0:
            self.reporter.error(n.Nodo(**_pos(ctx)), "tipo", "La longitud de VARCHAR debe ser mayor que 0")
            longitud = 1
        return TipoSQL("VARCHAR", longitud)

    def visitDropTable(self, ctx: SQLParser.DropTableContext) -> n.DropTable:
        return n.DropTable(self._id(ctx.identifier()), si_existe=ctx.IF() is not None, **_pos(ctx))

    def visitCreateIndex(self, ctx: SQLParser.CreateIndexContext) -> n.CreateIndex:
        ids = ctx.identifier()
        return n.CreateIndex(self._id(ids[0]), self._id(ids[1]), self._id(ids[2]), unico=ctx.UNIQUE() is not None,
                             pos_tabla=n.Nodo(**_pos(ids[1])), pos_columna=n.Nodo(**_pos(ids[2])), **_pos(ctx))

    def visitDropIndex(self, ctx: SQLParser.DropIndexContext) -> n.DropIndex:
        return n.DropIndex(self._id(ctx.identifier()), si_existe=ctx.IF() is not None, **_pos(ctx))

    # --- DML -------------------------------------------------------------

    def visitInsertStmt(self, ctx: SQLParser.InsertStmtContext) -> n.Insert:
        columnas = self._lista_ids(ctx.identifierList()) if ctx.identifierList() is not None else None
        posiciones = {
            "pos_tabla": n.Nodo(**_pos(ctx.identifier())),
            "pos_columnas": [n.Nodo(**_pos(i)) for i in ctx.identifierList().identifier()]
            if ctx.identifierList() is not None else [],
        }
        if ctx.selectStmt() is not None:
            consulta = self.visit(ctx.selectStmt())
            consulta.texto = _texto(ctx.selectStmt())
            return n.Insert(self._id(ctx.identifier()), columnas, None, consulta, **posiciones, **_pos(ctx))
        filas = [[self.visit(e) for e in fila.expr()] for fila in ctx.valuesRow()]
        return n.Insert(self._id(ctx.identifier()), columnas, filas, None, **posiciones, **_pos(ctx))

    def visitUpdateStmt(self, ctx: SQLParser.UpdateStmtContext) -> n.Update:
        asignaciones = [n.Assignment(self._id(a.identifier()), self.visit(a.expr()), **_pos(a))
                        for a in ctx.assignment()]
        where = self.visit(ctx.whereClause().expr()) if ctx.whereClause() is not None else None
        return n.Update(self._id(ctx.identifier()), asignaciones, where, pos_tabla=n.Nodo(**_pos(ctx.identifier())),
                        **_pos(ctx))

    def visitDeleteStmt(self, ctx: SQLParser.DeleteStmtContext) -> n.Delete:
        where = self.visit(ctx.whereClause().expr()) if ctx.whereClause() is not None else None
        return n.Delete(self._id(ctx.identifier()), where, pos_tabla=n.Nodo(**_pos(ctx.identifier())), **_pos(ctx))

    # --- SELECT ----------------------------------------------------------

    def visitSelectStmt(self, ctx: SQLParser.SelectStmtContext) -> n.Select:
        items = [self.visit(i) for i in ctx.selectItem()]
        desde = self.visit(ctx.fromClause()) if ctx.fromClause() is not None else []
        where = self.visit(ctx.whereClause().expr()) if ctx.whereClause() is not None else None
        group_by = [self.visit(e) for e in ctx.groupByClause().expr()] if ctx.groupByClause() is not None else []
        having = self.visit(ctx.havingClause().expr()) if ctx.havingClause() is not None else None
        order_by = []
        if ctx.orderByClause() is not None:
            for item in ctx.orderByClause().orderItem():
                order_by.append(n.OrderItem(self.visit(item.expr()), item.DESC() is not None, **_pos(item)))
        limit = offset = None
        if ctx.limitClause() is not None:
            numeros = ctx.limitClause().INT_LIT()
            limit = int(numeros[0].getText())
            offset = int(numeros[1].getText()) if len(numeros) > 1 else None
        return n.Select(ctx.DISTINCT() is not None, items, desde, where, group_by, having, order_by, limit, offset,
                        texto=_texto(ctx), **_pos(ctx))

    def visitSelectAll(self, ctx) -> n.Star:
        return n.Star(None, **_pos(ctx))

    def visitSelectTableAll(self, ctx: SQLParser.SelectTableAllContext) -> n.Star:
        return n.Star(self._id(ctx.identifier()), **_pos(ctx))

    def visitSelectExpr(self, ctx: SQLParser.SelectExprContext) -> n.SelectExpr:
        alias = self._id(ctx.identifier()) if ctx.identifier() is not None else None
        return n.SelectExpr(self.visit(ctx.expr()), alias, **_pos(ctx))

    def visitFromClause(self, ctx: SQLParser.FromClauseContext) -> list[n.FromItem]:
        tabla, alias = self._tabla_ref(ctx.tableRef())
        desde = [n.FromItem(tabla, alias, "BASE", None, **_pos(ctx.tableRef()))]
        for extra in ctx.fromExtra():
            tabla, alias = self._tabla_ref(extra.tableRef())
            if isinstance(extra, SQLParser.JoinItemContext):
                union = "LEFT" if extra.joinType() is not None and extra.joinType().LEFT() is not None else "INNER"
                desde.append(n.FromItem(tabla, alias, union, self.visit(extra.expr()), **_pos(extra.tableRef())))
            else:
                desde.append(n.FromItem(tabla, alias, "CROSS", None, **_pos(extra.tableRef())))
        return desde

    def _tabla_ref(self, ctx: SQLParser.TableRefContext) -> tuple[str, str]:
        ids = ctx.identifier()
        tabla = self._id(ids[0])
        return tabla, (self._id(ids[1]) if len(ids) > 1 else tabla)

    # ------------------------------------------------------------------
    # expresiones
    # ------------------------------------------------------------------

    def _expr(self, nodo: n.Expr, ctx) -> n.Expr:
        nodo.linea, nodo.columna = ctx.start.line, ctx.start.column + 1
        nodo.texto = _texto(ctx)
        return nodo

    def visitNotExpr(self, ctx: SQLParser.NotExprContext):
        interno = self.visit(ctx.expr())
        if isinstance(interno, n.Exists):
            return self._expr(n.Exists(interno.consulta, not interno.negado), ctx)
        return self._expr(n.UnaryOp("NOT", interno), ctx)

    def visitAndExpr(self, ctx: SQLParser.AndExprContext):
        return self._expr(n.BinaryOp("AND", self.visit(ctx.expr(0)), self.visit(ctx.expr(1))), ctx)

    def visitOrExpr(self, ctx: SQLParser.OrExprContext):
        return self._expr(n.BinaryOp("OR", self.visit(ctx.expr(0)), self.visit(ctx.expr(1))), ctx)

    def visitPredicateExpr(self, ctx):
        return self.visit(ctx.predicate())

    def visitComparePred(self, ctx: SQLParser.ComparePredContext):
        op = ctx.op.text
        op = "<>" if op == "!=" else op
        return self._expr(n.BinaryOp(op, self.visit(ctx.valueExpr(0)), self.visit(ctx.valueExpr(1))), ctx)

    def visitIsNullPred(self, ctx: SQLParser.IsNullPredContext):
        return self._expr(n.IsNull(self.visit(ctx.valueExpr()), ctx.NOT() is not None), ctx)

    def visitBetweenPred(self, ctx: SQLParser.BetweenPredContext):
        v = ctx.valueExpr()
        return self._expr(n.Between(self.visit(v[0]), self.visit(v[1]), self.visit(v[2]), ctx.NOT() is not None), ctx)

    def visitLikePred(self, ctx: SQLParser.LikePredContext):
        v = ctx.valueExpr()
        return self._expr(n.Like(self.visit(v[0]), self.visit(v[1]), ctx.NOT() is not None), ctx)

    def visitInSubqueryPred(self, ctx: SQLParser.InSubqueryPredContext):
        return self._expr(n.InSubquery(self.visit(ctx.valueExpr()), self.visit(ctx.selectStmt()),
                                       ctx.NOT() is not None), ctx)

    def visitInListPred(self, ctx: SQLParser.InListPredContext):
        v = ctx.valueExpr()
        return self._expr(n.InList(self.visit(v[0]), [self.visit(x) for x in v[1:]], ctx.NOT() is not None), ctx)

    def visitExistsPred(self, ctx: SQLParser.ExistsPredContext):
        return self._expr(n.Exists(self.visit(ctx.selectStmt()), False), ctx)

    def visitValuePred(self, ctx):
        return self.visit(ctx.valueExpr())

    def visitUnaryValue(self, ctx: SQLParser.UnaryValueContext):
        operando = self.visit(ctx.valueExpr())
        if ctx.op.text == "+":
            return operando
        if isinstance(operando, n.Literal) and operando.tipo_literal.es_numerico:
            return self._expr(n.Literal(-operando.valor, operando.tipo_literal), ctx)
        return self._expr(n.UnaryOp("-", operando), ctx)

    def visitMulValue(self, ctx: SQLParser.MulValueContext):
        return self._expr(n.BinaryOp(ctx.op.text, self.visit(ctx.valueExpr(0)), self.visit(ctx.valueExpr(1))), ctx)

    def visitAddValue(self, ctx: SQLParser.AddValueContext):
        return self._expr(n.BinaryOp(ctx.op.text, self.visit(ctx.valueExpr(0)), self.visit(ctx.valueExpr(1))), ctx)

    def visitConcatValue(self, ctx: SQLParser.ConcatValueContext):
        return self._expr(n.BinaryOp("||", self.visit(ctx.valueExpr(0)), self.visit(ctx.valueExpr(1))), ctx)

    def visitPrimaryValue(self, ctx):
        return self.visit(ctx.primary())

    def visitSubqueryPrimary(self, ctx: SQLParser.SubqueryPrimaryContext):
        return self._expr(n.ScalarSubquery(self.visit(ctx.selectStmt())), ctx)

    def visitParenPrimary(self, ctx: SQLParser.ParenPrimaryContext):
        return self.visit(ctx.expr())

    def visitAggregatePrimary(self, ctx):
        return self.visit(ctx.aggregate())

    def visitLiteralPrimary(self, ctx):
        return self.visit(ctx.literal())

    def visitColumnPrimary(self, ctx):
        return self.visit(ctx.columnRef())

    def visitCountStar(self, ctx):
        return self._expr(n.Aggregate("COUNT", None, False), ctx)

    def visitAggregateCall(self, ctx: SQLParser.AggregateCallContext):
        return self._expr(n.Aggregate(ctx.func.text.upper(), self.visit(ctx.expr()), ctx.DISTINCT() is not None), ctx)

    def visitColumnRef(self, ctx: SQLParser.ColumnRefContext):
        ids = ctx.identifier()
        if len(ids) == 2:
            return self._expr(n.ColumnRef(self._id(ids[0]), self._id(ids[1])), ctx)
        return self._expr(n.ColumnRef(None, self._id(ids[0])), ctx)

    # --- literales -------------------------------------------------------

    def visitSignedLiteral(self, ctx: SQLParser.SignedLiteralContext):
        lit = self.visit(ctx.literal())
        if ctx.MINUS() is not None:
            if not lit.tipo_literal.es_numerico:
                self.reporter.error(lit, "tipo", f"No se puede negar un valor {lit.tipo_literal}")
            else:
                lit = self._expr(n.Literal(-lit.valor, lit.tipo_literal), ctx)
        return lit

    def visitIntLiteral(self, ctx):
        return self._expr(n.Literal(int(ctx.getText()), INT), ctx)

    def visitFloatLiteral(self, ctx):
        return self._expr(n.Literal(float(ctx.getText()), FLOAT), ctx)

    def visitStringLiteral(self, ctx):
        return self._expr(n.Literal(_cadena(ctx.STRING_LIT().getText()), VARCHAR), ctx)

    def visitDateLiteral(self, ctx: SQLParser.DateLiteralContext):
        texto = _cadena(ctx.STRING_LIT().getText())
        fecha = parsear_fecha(texto)
        lit = self._expr(n.Literal(fecha, DATE), ctx)
        if fecha is None:
            self.reporter.error(lit, "valor", f"'{texto}' no es una fecha válida (formato YYYY-MM-DD)")
        return lit

    def visitBoolLiteral(self, ctx):
        return self._expr(n.Literal(ctx.TRUE() is not None, BOOLEAN), ctx)

    def visitNullLiteral(self, ctx):
        return self._expr(n.Literal(None, NULO), ctx)


def _cadena(token_texto: str) -> str:
    """'it''s' -> it's"""
    return token_texto[1:-1].replace("''", "'")


def construir_ast(tree) -> tuple[n.Script, list]:
    builder = ASTBuilder()
    script = builder.visit(tree)
    return script, builder.reporter.all()
