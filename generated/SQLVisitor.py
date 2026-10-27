# Generated from SQL.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .SQLParser import SQLParser
else:
    from SQLParser import SQLParser

# This class defines a complete generic visitor for a parse tree produced by SQLParser.

class SQLVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by SQLParser#script.
    def visitScript(self, ctx:SQLParser.ScriptContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#statement.
    def visitStatement(self, ctx:SQLParser.StatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#createTable.
    def visitCreateTable(self, ctx:SQLParser.CreateTableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#tableElement.
    def visitTableElement(self, ctx:SQLParser.TableElementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#columnDef.
    def visitColumnDef(self, ctx:SQLParser.ColumnDefContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#intType.
    def visitIntType(self, ctx:SQLParser.IntTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#floatType.
    def visitFloatType(self, ctx:SQLParser.FloatTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#varcharType.
    def visitVarcharType(self, ctx:SQLParser.VarcharTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#booleanType.
    def visitBooleanType(self, ctx:SQLParser.BooleanTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#dateType.
    def visitDateType(self, ctx:SQLParser.DateTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#pkConstraint.
    def visitPkConstraint(self, ctx:SQLParser.PkConstraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#notNullConstraint.
    def visitNotNullConstraint(self, ctx:SQLParser.NotNullConstraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#nullConstraint.
    def visitNullConstraint(self, ctx:SQLParser.NullConstraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#uniqueConstraint.
    def visitUniqueConstraint(self, ctx:SQLParser.UniqueConstraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#defaultConstraint.
    def visitDefaultConstraint(self, ctx:SQLParser.DefaultConstraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#referencesConstraint.
    def visitReferencesConstraint(self, ctx:SQLParser.ReferencesConstraintContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#tablePk.
    def visitTablePk(self, ctx:SQLParser.TablePkContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#tableUnique.
    def visitTableUnique(self, ctx:SQLParser.TableUniqueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#tableFk.
    def visitTableFk(self, ctx:SQLParser.TableFkContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#dropTable.
    def visitDropTable(self, ctx:SQLParser.DropTableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#createIndex.
    def visitCreateIndex(self, ctx:SQLParser.CreateIndexContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#dropIndex.
    def visitDropIndex(self, ctx:SQLParser.DropIndexContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#insertStmt.
    def visitInsertStmt(self, ctx:SQLParser.InsertStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#valuesRow.
    def visitValuesRow(self, ctx:SQLParser.ValuesRowContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#updateStmt.
    def visitUpdateStmt(self, ctx:SQLParser.UpdateStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#assignment.
    def visitAssignment(self, ctx:SQLParser.AssignmentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#deleteStmt.
    def visitDeleteStmt(self, ctx:SQLParser.DeleteStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#selectStmt.
    def visitSelectStmt(self, ctx:SQLParser.SelectStmtContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#selectAll.
    def visitSelectAll(self, ctx:SQLParser.SelectAllContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#selectTableAll.
    def visitSelectTableAll(self, ctx:SQLParser.SelectTableAllContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#selectExpr.
    def visitSelectExpr(self, ctx:SQLParser.SelectExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#fromClause.
    def visitFromClause(self, ctx:SQLParser.FromClauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#crossItem.
    def visitCrossItem(self, ctx:SQLParser.CrossItemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#crossJoinItem.
    def visitCrossJoinItem(self, ctx:SQLParser.CrossJoinItemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#joinItem.
    def visitJoinItem(self, ctx:SQLParser.JoinItemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#joinType.
    def visitJoinType(self, ctx:SQLParser.JoinTypeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#tableRef.
    def visitTableRef(self, ctx:SQLParser.TableRefContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#whereClause.
    def visitWhereClause(self, ctx:SQLParser.WhereClauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#groupByClause.
    def visitGroupByClause(self, ctx:SQLParser.GroupByClauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#havingClause.
    def visitHavingClause(self, ctx:SQLParser.HavingClauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#orderByClause.
    def visitOrderByClause(self, ctx:SQLParser.OrderByClauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#orderItem.
    def visitOrderItem(self, ctx:SQLParser.OrderItemContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#limitClause.
    def visitLimitClause(self, ctx:SQLParser.LimitClauseContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#predicateExpr.
    def visitPredicateExpr(self, ctx:SQLParser.PredicateExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#notExpr.
    def visitNotExpr(self, ctx:SQLParser.NotExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#orExpr.
    def visitOrExpr(self, ctx:SQLParser.OrExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#andExpr.
    def visitAndExpr(self, ctx:SQLParser.AndExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#comparePred.
    def visitComparePred(self, ctx:SQLParser.ComparePredContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#isNullPred.
    def visitIsNullPred(self, ctx:SQLParser.IsNullPredContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#betweenPred.
    def visitBetweenPred(self, ctx:SQLParser.BetweenPredContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#likePred.
    def visitLikePred(self, ctx:SQLParser.LikePredContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#inSubqueryPred.
    def visitInSubqueryPred(self, ctx:SQLParser.InSubqueryPredContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#inListPred.
    def visitInListPred(self, ctx:SQLParser.InListPredContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#existsPred.
    def visitExistsPred(self, ctx:SQLParser.ExistsPredContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#valuePred.
    def visitValuePred(self, ctx:SQLParser.ValuePredContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#primaryValue.
    def visitPrimaryValue(self, ctx:SQLParser.PrimaryValueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#concatValue.
    def visitConcatValue(self, ctx:SQLParser.ConcatValueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#mulValue.
    def visitMulValue(self, ctx:SQLParser.MulValueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#unaryValue.
    def visitUnaryValue(self, ctx:SQLParser.UnaryValueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#addValue.
    def visitAddValue(self, ctx:SQLParser.AddValueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#subqueryPrimary.
    def visitSubqueryPrimary(self, ctx:SQLParser.SubqueryPrimaryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#parenPrimary.
    def visitParenPrimary(self, ctx:SQLParser.ParenPrimaryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#aggregatePrimary.
    def visitAggregatePrimary(self, ctx:SQLParser.AggregatePrimaryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#literalPrimary.
    def visitLiteralPrimary(self, ctx:SQLParser.LiteralPrimaryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#columnPrimary.
    def visitColumnPrimary(self, ctx:SQLParser.ColumnPrimaryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#countStar.
    def visitCountStar(self, ctx:SQLParser.CountStarContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#aggregateCall.
    def visitAggregateCall(self, ctx:SQLParser.AggregateCallContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#columnRef.
    def visitColumnRef(self, ctx:SQLParser.ColumnRefContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#signedLiteral.
    def visitSignedLiteral(self, ctx:SQLParser.SignedLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#intLiteral.
    def visitIntLiteral(self, ctx:SQLParser.IntLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#floatLiteral.
    def visitFloatLiteral(self, ctx:SQLParser.FloatLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#stringLiteral.
    def visitStringLiteral(self, ctx:SQLParser.StringLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#dateLiteral.
    def visitDateLiteral(self, ctx:SQLParser.DateLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#boolLiteral.
    def visitBoolLiteral(self, ctx:SQLParser.BoolLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#nullLiteral.
    def visitNullLiteral(self, ctx:SQLParser.NullLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#identifierList.
    def visitIdentifierList(self, ctx:SQLParser.IdentifierListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by SQLParser#identifier.
    def visitIdentifier(self, ctx:SQLParser.IdentifierContext):
        return self.visitChildren(ctx)



del SQLParser