"""
Analisis semantico de un script SQL completo, ANTES de ejecutar nada.

Trabaja sobre una COPIA del catalogo: cada CREATE/DROP se aplica a esa copia
de forma simulada, de modo que `CREATE TABLE t (...); INSERT INTO t ...` se
valida correctamente aunque la tabla aun no exista en disco.

Verifica (enunciado, "Analisis Semantico"):
  - tabla inexistente / duplicada                    -> categoria "tabla"
  - columna inexistente / duplicada                  -> "columna"
  - tipos incompatibles                              -> "tipo"
  - valores incorrectos en INSERT / UPDATE           -> "valor"
  - referencias ambiguas o invalidas (alias, FK)     -> "referencia"
  - indice inexistente o duplicado                   -> "indice"
  - subconsulta escalar / IN con mas de una columna  -> "subconsulta"
  - agregaciones fuera de lugar, GROUP BY            -> "agregacion"
(Que una subconsulta escalar retorne mas de un REGISTRO depende de los datos:
eso lo detecta el interprete en tiempo de ejecucion.)

Ademas ANOTA el AST para el interprete: cada ColumnRef queda resuelta
(`ref_alias`, `ref_nivel`), cada expresion con su `tipo`, cada SELECT con sus
`columnas_salida`, si es `agrupado` y si es `correlacionada`, y cada ORDER BY
que se refiere a una columna del resultado con su `indice_salida`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from core.errors import ErrorReporter, SQLError
from core.types import BOOLEAN, DATE, FLOAT, INT, NULO, VARCHAR, TipoSQL, asignable, comparables, parsear_fecha, \
    tipo_comun

from almacenamiento.catalog import SIN_DEFAULT, Catalog, Columna, Indice, LlaveForanea, Tabla
from arbol import nodes as n


# ---------------------------------------------------------------------------
# Alcances
# ---------------------------------------------------------------------------

@dataclass
class Fuente:
    alias: str
    tabla: Tabla


@dataclass
class Alcance:
    fuentes: list[Fuente] = field(default_factory=list)
    padre: "Alcance | None" = None
    incompleto: bool = False  # alguna tabla del FROM no existe: no se reportan columnas en cascada

    def por_alias(self, alias: str) -> Fuente | None:
        return next((f for f in self.fuentes if f.alias == alias), None)


@dataclass
class Ctx:
    clausula: str
    agregados: bool = False
    en_agregado: bool = False


def construir_tabla(nodo: n.CreateTable) -> Tabla:
    """Esquema del catalogo a partir del CREATE TABLE (lo usa tambien el interprete)."""
    pk = list(nodo.primary_key) or [c.nombre for c in nodo.columnas if c.primary_key][:1]
    columnas = []
    for c in nodo.columnas:
        col = Columna(c.nombre, c.tipo_dato, c.not_null or c.nombre in pk)
        if c.default is not None:
            col.default = c.default.valor
        columnas.append(col)
    uniques = [[c.nombre] for c in nodo.columnas if c.unique and [c.nombre] != pk]
    uniques += [u for u in nodo.uniques if u != pk and u not in uniques]
    foraneas = [LlaveForanea(fk.columna_local, fk.tabla_ref, fk.columna_ref) for fk in nodo.foraneas]
    return Tabla(nodo.nombre, columnas, pk, uniques, foraneas)


class SemanticAnalyzer:
    def __init__(self, catalogo: Catalog):
        self.catalogo = catalogo.copia()
        self.reporter = ErrorReporter()
        self._pila_selects: list[n.Select] = []

    def analizar(self, script: n.Script) -> list[SQLError]:
        for sentencia in script.sentencias:
            self.sentencia(sentencia)
        return self.reporter.all()

    def sentencia(self, s: n.Sentencia) -> None:
        metodo = {
            n.CreateTable: self._create_table,
            n.DropTable: self._drop_table,
            n.CreateIndex: self._create_index,
            n.DropIndex: self._drop_index,
            n.Insert: self._insert,
            n.Update: self._update,
            n.Delete: self._delete,
            n.Select: lambda sel: self._select(sel, None),
        }[type(s)]
        metodo(s)

    def _error(self, nodo, categoria: str, mensaje: str) -> None:
        self.reporter.error(nodo, categoria, mensaje)

    # ------------------------------------------------------------------
    # DDL
    # ------------------------------------------------------------------

    def _create_table(self, s: n.CreateTable) -> None:
        if self.catalogo.tabla(s.nombre) is not None:
            if not s.si_no_existe:
                self._error(s, "tabla", f"La tabla '{s.nombre}' ya existe")
            return

        nombres: dict[str, n.ColumnDef] = {}
        for col in s.columnas:
            if col.nombre in nombres:
                self._error(col, "columna", f"La columna '{col.nombre}' está definida más de una vez")
            nombres.setdefault(col.nombre, col)

        pks_columna = [c for c in s.columnas if c.primary_key]
        if len(pks_columna) > 1 or (pks_columna and s.primary_key):
            self._error(pks_columna[-1], "tabla", f"La tabla '{s.nombre}' tiene más de una PRIMARY KEY")
        for lista, que in [(s.primary_key, "PRIMARY KEY"), *[(u, "UNIQUE") for u in s.uniques]]:
            for nombre in lista:
                if nombre not in nombres:
                    self._error(s, "columna", f"{que}: la columna '{nombre}' no existe en '{s.nombre}'")
            if len(set(lista)) != len(lista):
                self._error(s, "columna", f"{que}: hay columnas repetidas en ({', '.join(lista)})")

        for col in s.columnas:
            if col.default is not None:
                self._verificar_valor(col.default, col.default.tipo_literal, Columna(col.nombre, col.tipo_dato,
                                      col.not_null or col.primary_key), "DEFAULT")

        nueva = construir_tabla(s)
        for fk in s.foraneas:
            local = nombres.get(fk.columna_local)
            if local is None:
                self._error(fk, "columna", f"FOREIGN KEY: la columna '{fk.columna_local}' no existe en '{s.nombre}'")
                continue
            ref = nueva if fk.tabla_ref == s.nombre else self.catalogo.tabla(fk.tabla_ref)
            if ref is None:
                self._error(fk, "tabla", f"FOREIGN KEY: la tabla referenciada '{fk.tabla_ref}' no existe")
                continue
            col_ref = ref.columna(fk.columna_ref)
            if col_ref is None:
                self._error(fk, "columna", f"FOREIGN KEY: la columna '{fk.columna_ref}' no existe en '{fk.tabla_ref}'")
                continue
            if not ref.es_unica(fk.columna_ref):
                self._error(fk, "referencia", f"FOREIGN KEY: '{fk.tabla_ref}.{fk.columna_ref}' debe ser PRIMARY KEY "
                                              "o UNIQUE para poder referenciarse")
            if not comparables(local.tipo_dato, col_ref.tipo):
                self._error(fk, "tipo", f"FOREIGN KEY: '{fk.columna_local}' es {local.tipo_dato} pero "
                                        f"'{fk.tabla_ref}.{fk.columna_ref}' es {col_ref.tipo}")

        nueva.columnas = [c for i, c in enumerate(nueva.columnas)
                          if c.nombre not in [x.nombre for x in nueva.columnas[:i]]]
        self.catalogo.tablas[s.nombre] = nueva

    def _drop_table(self, s: n.DropTable) -> None:
        if self.catalogo.tabla(s.nombre) is None:
            if not s.si_existe:
                self._error(s, "tabla", f"La tabla '{s.nombre}' no existe")
            return
        referencias = self.catalogo.referencias_a(s.nombre)
        if referencias:
            hija, fk = referencias[0]
            self._error(s, "referencia", f"No se puede eliminar '{s.nombre}': la tabla '{hija}' la referencia "
                                         f"(FOREIGN KEY {fk.columna})")
            return
        self.catalogo.eliminar_tabla(s.nombre)

    def _create_index(self, s: n.CreateIndex) -> None:
        if s.nombre in self.catalogo.indices:
            self._error(s, "indice", f"El índice '{s.nombre}' ya existe")
            return
        tabla = self.catalogo.tabla(s.tabla)
        if tabla is None:
            self._error(s.pos_tabla or s, "tabla", f"La tabla '{s.tabla}' no existe")
            return
        if tabla.columna(s.columna_indice) is None:
            self._error(s.pos_columna or s, "columna", f"La columna '{s.columna_indice}' no existe en la tabla "
                                                       f"'{s.tabla}'")
            return
        existente = self.catalogo.indice_sobre(s.tabla, s.columna_indice)
        if existente is not None:
            self._error(s, "indice", f"Ya existe el índice '{existente.nombre}' sobre {s.tabla}({s.columna_indice})")
            return
        self.catalogo.indices[s.nombre] = Indice(s.nombre, s.tabla, s.columna_indice, s.unico)

    def _drop_index(self, s: n.DropIndex) -> None:
        if s.nombre not in self.catalogo.indices:
            if not s.si_existe:
                self._error(s, "indice", f"El índice '{s.nombre}' no existe")
            return
        del self.catalogo.indices[s.nombre]

    # ------------------------------------------------------------------
    # DML
    # ------------------------------------------------------------------

    def _verificar_valor(self, expr: n.Expr, tipo: TipoSQL, columna: Columna, donde: str) -> None:
        """Valor (ya tipado) que se guardara en `columna`: tipos, NULL y longitud de literales."""
        tipo = self._coaccionar_fecha(expr, tipo, columna.tipo)
        if isinstance(expr, n.Literal) and expr.valor is None and columna.not_null:
            self._error(expr, "valor", f"{donde}: la columna '{columna.nombre}' no admite NULL")
            return
        if not asignable(columna.tipo, tipo):
            self._error(expr, "tipo", f"{donde}: no se puede asignar un valor {tipo} a la columna "
                                      f"'{columna.nombre}' de tipo {columna.tipo}")
            return
        if (isinstance(expr, n.Literal) and type(expr.valor) is str and columna.tipo.longitud is not None
                and len(expr.valor) > columna.tipo.longitud):
            self._error(expr, "valor", f"{donde}: el texto '{expr.valor}' tiene {len(expr.valor)} caracteres y la "
                                       f"columna '{columna.nombre}' es {columna.tipo}")

    def _insert(self, s: n.Insert) -> None:
        tabla = self.catalogo.tabla(s.tabla)
        if tabla is None:
            self._error(s.pos_tabla or s, "tabla", f"La tabla '{s.tabla}' no existe")
            if s.consulta is not None:
                self._select(s.consulta, None)
            return

        if s.columnas is None:
            destino = list(tabla.columnas)
        else:
            destino = []
            vistos = set()
            for i, nombre in enumerate(s.columnas):
                col = tabla.columna(nombre)
                pos = s.pos_columnas[i] if i < len(s.pos_columnas or []) else s
                if col is None:
                    self._error(pos, "columna", f"La columna '{nombre}' no existe en la tabla '{s.tabla}'")
                elif nombre in vistos:
                    self._error(pos, "columna", f"La columna '{nombre}' se repite en la lista del INSERT")
                else:
                    destino.append(col)
                vistos.add(nombre)
            if len(destino) != len(s.columnas):
                return
            for col in tabla.columnas:
                if col.nombre not in vistos and col.not_null and col.default is SIN_DEFAULT:
                    self._error(s, "valor", f"La columna '{col.nombre}' es NOT NULL y no tiene DEFAULT: "
                                            "debe incluirse en el INSERT")

        if s.consulta is not None:
            columnas = self._select(s.consulta, None)
            if columnas is not None and len(columnas) != len(destino):
                self._error(s.consulta, "valor", f"El SELECT retorna {len(columnas)} columna(s) pero el INSERT "
                                                 f"espera {len(destino)}")
            elif columnas is not None:
                for col_sal, col in zip(columnas, destino):
                    if not asignable(col.tipo, col_sal.tipo):
                        self._error(s.consulta, "tipo", f"No se puede insertar la columna '{col_sal.nombre}' "
                                                        f"({col_sal.tipo}) en '{col.nombre}' ({col.tipo})")
            return

        vacio = Alcance()
        for i, fila in enumerate(s.filas, start=1):
            if len(fila) != len(destino):
                nodo = fila[0] if fila else s
                self._error(nodo, "valor", f"La fila {i} de VALUES tiene {len(fila)} valor(es) pero se esperaban "
                                           f"{len(destino)}")
                for expr in fila:
                    self._tipo(expr, vacio, Ctx("VALUES"))
                continue
            for expr, col in zip(fila, destino):
                tipo = self._tipo(expr, vacio, Ctx("VALUES"))
                self._verificar_valor(expr, tipo, col, "INSERT")

    def _alcance_tabla(self, nombre: str, nodo) -> Alcance | None:
        nodo = getattr(nodo, "pos_tabla", None) or nodo
        tabla = self.catalogo.tabla(nombre)
        if tabla is None:
            self._error(nodo, "tabla", f"La tabla '{nombre}' no existe")
            return None
        return Alcance([Fuente(nombre, tabla)])

    def _update(self, s: n.Update) -> None:
        alcance = self._alcance_tabla(s.tabla, s)
        if alcance is None:
            return
        tabla = alcance.fuentes[0].tabla
        vistas = set()
        for asig in s.asignaciones:
            tipo = self._tipo(asig.valor, alcance, Ctx("SET"))
            col = tabla.columna(asig.columna_destino)
            if col is None:
                self._error(asig, "columna", f"La columna '{asig.columna_destino}' no existe en la tabla '{s.tabla}'")
                continue
            if asig.columna_destino in vistas:
                self._error(asig, "columna", f"La columna '{asig.columna_destino}' se asigna más de una vez")
            vistas.add(asig.columna_destino)
            self._verificar_valor(asig.valor, tipo, col, "UPDATE")
        self._condicion(s.where, alcance, "WHERE")

    def _delete(self, s: n.Delete) -> None:
        alcance = self._alcance_tabla(s.tabla, s)
        if alcance is not None:
            self._condicion(s.where, alcance, "WHERE")

    def _condicion(self, expr: n.Expr | None, alcance: Alcance, clausula: str, agregados: bool = False) -> None:
        if expr is None:
            return
        tipo = self._tipo(expr, alcance, Ctx(clausula, agregados))
        if tipo not in (BOOLEAN, NULO):
            self._error(expr, "tipo", f"La condición de {clausula} debe ser BOOLEAN, pero es {tipo}")

    # ------------------------------------------------------------------
    # SELECT
    # ------------------------------------------------------------------

    def _select(self, sel: n.Select, padre: Alcance | None) -> list[n.ColumnaSalida] | None:
        self._pila_selects.append(sel)
        try:
            return self._select_interno(sel, padre)
        finally:
            self._pila_selects.pop()

    def _select_interno(self, sel: n.Select, padre: Alcance | None) -> list[n.ColumnaSalida]:
        alcance = Alcance(padre=padre)
        for item in sel.desde:
            tabla = self.catalogo.tabla(item.tabla)
            if tabla is None:
                self._error(item, "tabla", f"La tabla '{item.tabla}' no existe")
                alcance.incompleto = True
            elif alcance.por_alias(item.alias) is not None:
                self._error(item, "referencia", f"El alias '{item.alias}' se usa más de una vez en el FROM")
            else:
                alcance.fuentes.append(Fuente(item.alias, tabla))
            if item.condicion is not None:
                self._condicion(item.condicion, alcance, "ON")

        self._condicion(sel.where, alcance, "WHERE")
        for expr in sel.group_by:
            self._tipo(expr, alcance, Ctx("GROUP BY"))

        exprs_nivel = [i.expr for i in sel.items if isinstance(i, n.SelectExpr)] + [o.expr for o in sel.order_by]
        if sel.having is not None:
            exprs_nivel.append(sel.having)
        sel.agrupado = bool(sel.group_by) or sel.having is not None or any(_tiene_agregado(e) for e in exprs_nivel)

        columnas: list[n.ColumnaSalida] = []
        for item in sel.items:
            if isinstance(item, n.Star):
                columnas.extend(self._expandir_estrella(item, alcance))
                continue
            tipo = self._tipo(item.expr, alcance, Ctx("SELECT", agregados=True))
            if item.alias:
                nombre = item.alias
            elif isinstance(item.expr, n.ColumnRef):
                nombre = item.expr.nombre
            else:
                nombre = item.expr.texto
            columnas.append(n.ColumnaSalida(nombre, tipo, item.expr))

        if sel.having is not None:
            self._condicion(sel.having, alcance, "HAVING", agregados=True)

        aliases = {item.alias: i for i, item in enumerate(sel.items) if isinstance(item, n.SelectExpr) and item.alias}
        orden_exprs = []
        for orden in sel.order_by:
            e = orden.expr
            if isinstance(e, n.ColumnRef) and e.tabla is None and e.nombre in aliases:
                orden.indice_salida = _posicion_salida(sel.items, aliases[e.nombre], columnas)
                e.tipo = columnas[orden.indice_salida].tipo
            elif isinstance(e, n.Literal) and e.tipo_literal == INT:
                if not 1 <= e.valor <= len(columnas):
                    self._error(e, "referencia", f"ORDER BY {e.valor}: el resultado solo tiene {len(columnas)} "
                                                 "columna(s)")
                else:
                    orden.indice_salida = e.valor - 1
            else:
                self._tipo(e, alcance, Ctx("ORDER BY", agregados=sel.agrupado))
                orden_exprs.append(e)

        if sel.agrupado:
            for col in columnas:
                self._validar_agrupado(col.expr, sel.group_by, "SELECT")
            if sel.having is not None:
                self._validar_agrupado(sel.having, sel.group_by, "HAVING")
            for e in orden_exprs:
                self._validar_agrupado(e, sel.group_by, "ORDER BY")

        sel.columnas_salida = columnas
        return columnas

    def _expandir_estrella(self, item: n.Star, alcance: Alcance) -> list[n.ColumnaSalida]:
        if item.tabla is None:
            fuentes = alcance.fuentes
            if not fuentes and not alcance.incompleto:
                self._error(item, "referencia", "SELECT * requiere una cláusula FROM")
        else:
            fuente = alcance.por_alias(item.tabla)
            if fuente is None:
                if not alcance.incompleto:
                    self._error(item, "referencia", f"La tabla o alias '{item.tabla}' no aparece en el FROM")
                return []
            fuentes = [fuente]
        salida = []
        for f in fuentes:
            for col in f.tabla.columnas:
                ref = n.ColumnRef(f.alias, col.nombre, linea=item.linea, columna=item.columna,
                                  texto=f"{f.alias}.{col.nombre}")
                ref.ref_alias, ref.ref_nivel, ref.tipo = f.alias, 0, col.tipo
                salida.append(n.ColumnaSalida(col.nombre, col.tipo, ref))
        return salida

    def _validar_agrupado(self, expr: n.Expr, grupos: list[n.Expr], clausula: str) -> None:
        if any(_misma_expr(expr, g) for g in grupos):
            return
        if isinstance(expr, (n.Aggregate, n.ScalarSubquery, n.Exists)):
            return
        if isinstance(expr, n.InSubquery):
            self._validar_agrupado(expr.expr, grupos, clausula)
            return
        if isinstance(expr, n.ColumnRef):
            if expr.ref_nivel == 0 and expr.ref_alias is not None:
                self._error(expr, "agregacion", f"{clausula}: la columna '{expr.texto or expr.nombre}' debe aparecer "
                                                "en GROUP BY o usarse dentro de una función de agregación")
            return
        for h in n.hijos(expr):
            if isinstance(h, n.Expr):
                self._validar_agrupado(h, grupos, clausula)

    # ------------------------------------------------------------------
    # expresiones
    # ------------------------------------------------------------------

    def _tipo(self, e: n.Expr, alcance: Alcance, ctx: Ctx) -> TipoSQL:
        tipo = self._tipo_interno(e, alcance, ctx)
        e.tipo = tipo
        return tipo

    def _tipo_interno(self, e: n.Expr, alcance: Alcance, ctx: Ctx) -> TipoSQL:
        if isinstance(e, n.Literal):
            return e.tipo_literal
        if isinstance(e, n.ColumnRef):
            return self._resolver(e, alcance)

        if isinstance(e, n.UnaryOp):
            t = self._tipo(e.operando, alcance, ctx)
            if e.op == "NOT":
                if t not in (BOOLEAN, NULO):
                    self._error(e, "tipo", f"NOT requiere un operando BOOLEAN (recibió {t})")
                return BOOLEAN
            if not (t.es_numerico or t.es_nulo):
                self._error(e, "tipo", f"El operador unario '{e.op}' requiere un número (recibió {t})")
                return INT
            return t

        if isinstance(e, n.BinaryOp):
            return self._binaria(e, alcance, ctx)

        if isinstance(e, n.IsNull):
            self._tipo(e.expr, alcance, ctx)
            return BOOLEAN

        if isinstance(e, n.Between):
            t = self._tipo(e.expr, alcance, ctx)
            for lado in (e.desde, e.hasta):
                t2 = self._coaccionar_fecha(lado, self._tipo(lado, alcance, ctx), t)
                if not comparables(t, t2):
                    self._error(lado, "tipo", f"Tipos incompatibles en BETWEEN: {t} y {t2}")
            return BOOLEAN

        if isinstance(e, n.Like):
            for lado in (e.expr, e.patron):
                t = self._tipo(lado, alcance, ctx)
                if t not in (VARCHAR, NULO) and t.nombre != "VARCHAR":
                    self._error(lado, "tipo", f"LIKE requiere operandos VARCHAR (recibió {t})")
            return BOOLEAN

        if isinstance(e, n.InList):
            t = self._tipo(e.expr, alcance, ctx)
            for v in e.valores:
                t2 = self._coaccionar_fecha(v, self._tipo(v, alcance, ctx), t)
                if not comparables(t, t2):
                    self._error(v, "tipo", f"Tipos incompatibles en IN: {t} y {t2}")
            return BOOLEAN

        if isinstance(e, n.InSubquery):
            t = self._tipo(e.expr, alcance, ctx)
            columnas = self._select(e.consulta, alcance)
            if len(columnas) != 1:
                self._error(e.consulta, "subconsulta", f"La subconsulta de IN debe retornar exactamente una columna "
                                                       f"(retorna {len(columnas)})")
            elif not comparables(t, columnas[0].tipo):
                self._error(e, "tipo", f"Tipos incompatibles en IN: {t} y {columnas[0].tipo} (subconsulta)")
            return BOOLEAN

        if isinstance(e, n.Exists):
            self._select(e.consulta, alcance)
            return BOOLEAN

        if isinstance(e, n.ScalarSubquery):
            columnas = self._select(e.consulta, alcance)
            if len(columnas) != 1:
                self._error(e, "subconsulta", f"La subconsulta escalar debe retornar exactamente una columna "
                                              f"(retorna {len(columnas)})")
                return NULO
            return columnas[0].tipo

        if isinstance(e, n.Aggregate):
            return self._agregado(e, alcance, ctx)

        raise AssertionError(f"expresion no soportada: {type(e).__name__}")

    def _binaria(self, e: n.BinaryOp, alcance: Alcance, ctx: Ctx) -> TipoSQL:
        ti = self._tipo(e.izquierda, alcance, ctx)
        td = self._tipo(e.derecha, alcance, ctx)
        op = e.op
        if op in ("AND", "OR"):
            for lado, t in ((e.izquierda, ti), (e.derecha, td)):
                if t not in (BOOLEAN, NULO):
                    self._error(lado, "tipo", f"{op} requiere operandos BOOLEAN (recibió {t})")
            return BOOLEAN
        if op in ("=", "<>", "<", "<=", ">", ">="):
            td = self._coaccionar_fecha(e.derecha, td, ti)
            ti = self._coaccionar_fecha(e.izquierda, ti, td)
            if not comparables(ti, td):
                self._error(e, "tipo", f"Tipos incompatibles: no se puede comparar {ti} con {td}")
            return BOOLEAN
        if op == "||":
            return VARCHAR
        # + - * / %
        if not ((ti.es_numerico or ti.es_nulo) and (td.es_numerico or td.es_nulo)):
            self._error(e, "tipo", f"El operador '{op}' requiere operandos numéricos (recibió {ti} y {td})")
            return INT
        if op == "/":
            return FLOAT
        comun = tipo_comun(ti, td)
        return INT if comun.es_nulo else comun

    def _agregado(self, e: n.Aggregate, alcance: Alcance, ctx: Ctx) -> TipoSQL:
        if ctx.en_agregado:
            self._error(e, "agregacion", f"No se pueden anidar funciones de agregación ({e.texto})")
        elif not ctx.agregados:
            self._error(e, "agregacion", f"No se permiten funciones de agregación en {ctx.clausula} ({e.texto})")
        if e.argumento is None:
            return INT
        interno = Ctx(ctx.clausula, agregados=False, en_agregado=True)
        t = self._tipo(e.argumento, alcance, interno)
        if e.funcion == "COUNT":
            return INT
        if e.funcion in ("SUM", "AVG"):
            if not (t.es_numerico or t.es_nulo):
                self._error(e, "tipo", f"{e.funcion} requiere una columna numérica (recibió {t})")
                return FLOAT
            return FLOAT if e.funcion == "AVG" else (INT if t.es_nulo else t)
        if t == BOOLEAN:
            self._error(e, "tipo", f"{e.funcion} no se puede aplicar a BOOLEAN")
        return t

    def _coaccionar_fecha(self, expr: n.Expr, tipo: TipoSQL, contra: TipoSQL) -> TipoSQL:
        """'2024-01-01' comparado/asignado con un DATE se convierte en un literal DATE."""
        if contra != DATE or tipo.nombre != "VARCHAR" or not isinstance(expr, n.Literal):
            return tipo
        fecha = parsear_fecha(expr.valor)
        if fecha is None:
            self._error(expr, "valor", f"'{expr.valor}' no es una fecha válida (formato YYYY-MM-DD)")
            return DATE
        expr.valor, expr.tipo_literal, expr.tipo = fecha, DATE, DATE
        return DATE

    def _resolver(self, ref: n.ColumnRef, alcance: Alcance) -> TipoSQL:
        nivel = 0
        a = alcance
        while a is not None:
            if ref.tabla is not None:
                fuente = a.por_alias(ref.tabla)
                if fuente is not None:
                    col = fuente.tabla.columna(ref.nombre)
                    if col is None:
                        self._error(ref, "columna", f"La columna '{ref.nombre}' no existe en la tabla "
                                                    f"'{fuente.tabla.nombre}'")
                        return NULO
                    return self._anotar(ref, fuente, nivel, col.tipo)
            else:
                candidatas = [f for f in a.fuentes if f.tabla.columna(ref.nombre) is not None]
                if len(candidatas) > 1:
                    nombres = ", ".join(f.alias for f in candidatas)
                    self._error(ref, "referencia", f"La columna '{ref.nombre}' es ambigua: existe en {nombres}; "
                                                   "califíquela con la tabla o el alias")
                if candidatas:
                    f = candidatas[0]
                    return self._anotar(ref, f, nivel, f.tabla.columna(ref.nombre).tipo)
            if a.incompleto:
                return NULO
            a = a.padre
            nivel += 1

        if ref.tabla is not None:
            self._error(ref, "referencia", f"La tabla o alias '{ref.tabla}' no aparece en el FROM de la consulta")
        elif alcance.fuentes:
            tablas = ", ".join(f"'{f.tabla.nombre}'" for f in alcance.fuentes)
            self._error(ref, "columna", f"La columna '{ref.nombre}' no existe en {tablas}")
        else:
            self._error(ref, "columna", f"La columna '{ref.nombre}' no existe (no hay tablas en este contexto)")
        return NULO

    def _anotar(self, ref: n.ColumnRef, fuente: Fuente, nivel: int, tipo: TipoSQL) -> TipoSQL:
        ref.ref_alias, ref.ref_nivel = fuente.alias, nivel
        for k in range(1, min(nivel, len(self._pila_selects)) + 1):
            self._pila_selects[-k].correlacionada = True
        return tipo


def _tiene_agregado(expr: n.Expr) -> bool:
    return any(isinstance(x, n.Aggregate) for x in n.recorrer(expr, entrar_subconsultas=False))


def _misma_expr(a: n.Expr, b: n.Expr) -> bool:
    if isinstance(a, n.ColumnRef) and isinstance(b, n.ColumnRef):
        return (a.ref_alias, a.nombre, a.ref_nivel) == (b.ref_alias, b.nombre, b.ref_nivel)
    return a == b


def _posicion_salida(items: list[n.SelectItem], indice_item: int, columnas: list[n.ColumnaSalida]) -> int:
    """Indice en columnas_salida del item `indice_item` (las * anteriores ocupan varias columnas)."""
    destino = items[indice_item].expr
    return next(i for i, c in enumerate(columnas) if c.expr is destino)
