# Generated from SQL.g4 by ANTLR 4.13.2
from antlr4 import *
if "." in __name__:
    from .SQLParser import SQLParser
else:
    from SQLParser import SQLParser

# This class defines a complete listener for a parse tree produced by SQLParser.
class SQLListener(ParseTreeListener):

    # Enter a parse tree produced by SQLParser#script.
    def enterScript(self, ctx:SQLParser.ScriptContext):
        pass

    # Exit a parse tree produced by SQLParser#script.
    def exitScript(self, ctx:SQLParser.ScriptContext):
        pass


    # Enter a parse tree produced by SQLParser#statement.
    def enterStatement(self, ctx:SQLParser.StatementContext):
        pass

    # Exit a parse tree produced by SQLParser#statement.
    def exitStatement(self, ctx:SQLParser.StatementContext):
        pass


    # Enter a parse tree produced by SQLParser#createTable.
    def enterCreateTable(self, ctx:SQLParser.CreateTableContext):
        pass

    # Exit a parse tree produced by SQLParser#createTable.
    def exitCreateTable(self, ctx:SQLParser.CreateTableContext):
        pass


    # Enter a parse tree produced by SQLParser#tableElement.
    def enterTableElement(self, ctx:SQLParser.TableElementContext):
        pass

    # Exit a parse tree produced by SQLParser#tableElement.
    def exitTableElement(self, ctx:SQLParser.TableElementContext):
        pass


    # Enter a parse tree produced by SQLParser#columnDef.
    def enterColumnDef(self, ctx:SQLParser.ColumnDefContext):
        pass

    # Exit a parse tree produced by SQLParser#columnDef.
    def exitColumnDef(self, ctx:SQLParser.ColumnDefContext):
        pass


    # Enter a parse tree produced by SQLParser#intType.
    def enterIntType(self, ctx:SQLParser.IntTypeContext):
        pass

    # Exit a parse tree produced by SQLParser#intType.
    def exitIntType(self, ctx:SQLParser.IntTypeContext):
        pass


    # Enter a parse tree produced by SQLParser#floatType.
    def enterFloatType(self, ctx:SQLParser.FloatTypeContext):
        pass

    # Exit a parse tree produced by SQLParser#floatType.
    def exitFloatType(self, ctx:SQLParser.FloatTypeContext):
        pass


    # Enter a parse tree produced by SQLParser#varcharType.
    def enterVarcharType(self, ctx:SQLParser.VarcharTypeContext):
        pass

    # Exit a parse tree produced by SQLParser#varcharType.
    def exitVarcharType(self, ctx:SQLParser.VarcharTypeContext):
        pass


    # Enter a parse tree produced by SQLParser#booleanType.
    def enterBooleanType(self, ctx:SQLParser.BooleanTypeContext):
        pass

    # Exit a parse tree produced by SQLParser#booleanType.
    def exitBooleanType(self, ctx:SQLParser.BooleanTypeContext):
        pass


    # Enter a parse tree produced by SQLParser#dateType.
    def enterDateType(self, ctx:SQLParser.DateTypeContext):
        pass

    # Exit a parse tree produced by SQLParser#dateType.
    def exitDateType(self, ctx:SQLParser.DateTypeContext):
        pass


    # Enter a parse tree produced by SQLParser#pkConstraint.
    def enterPkConstraint(self, ctx:SQLParser.PkConstraintContext):
        pass

    # Exit a parse tree produced by SQLParser#pkConstraint.
    def exitPkConstraint(self, ctx:SQLParser.PkConstraintContext):
        pass


    # Enter a parse tree produced by SQLParser#notNullConstraint.
    def enterNotNullConstraint(self, ctx:SQLParser.NotNullConstraintContext):
        pass

    # Exit a parse tree produced by SQLParser#notNullConstraint.
    def exitNotNullConstraint(self, ctx:SQLParser.NotNullConstraintContext):
        pass


    # Enter a parse tree produced by SQLParser#nullConstraint.
    def enterNullConstraint(self, ctx:SQLParser.NullConstraintContext):
        pass

    # Exit a parse tree produced by SQLParser#nullConstraint.
    def exitNullConstraint(self, ctx:SQLParser.NullConstraintContext):
        pass


    # Enter a parse tree produced by SQLParser#uniqueConstraint.
    def enterUniqueConstraint(self, ctx:SQLParser.UniqueConstraintContext):
        pass

    # Exit a parse tree produced by SQLParser#uniqueConstraint.
    def exitUniqueConstraint(self, ctx:SQLParser.UniqueConstraintContext):
        pass


    # Enter a parse tree produced by SQLParser#defaultConstraint.
    def enterDefaultConstraint(self, ctx:SQLParser.DefaultConstraintContext):
        pass

    # Exit a parse tree produced by SQLParser#defaultConstraint.
    def exitDefaultConstraint(self, ctx:SQLParser.DefaultConstraintContext):
        pass


    # Enter a parse tree produced by SQLParser#referencesConstraint.
    def enterReferencesConstraint(self, ctx:SQLParser.ReferencesConstraintContext):
        pass

    # Exit a parse tree produced by SQLParser#referencesConstraint.
    def exitReferencesConstraint(self, ctx:SQLParser.ReferencesConstraintContext):
        pass


    # Enter a parse tree produced by SQLParser#tablePk.
    def enterTablePk(self, ctx:SQLParser.TablePkContext):
        pass

    # Exit a parse tree produced by SQLParser#tablePk.
    def exitTablePk(self, ctx:SQLParser.TablePkContext):
        pass


    # Enter a parse tree produced by SQLParser#tableUnique.
    def enterTableUnique(self, ctx:SQLParser.TableUniqueContext):
        pass

    # Exit a parse tree produced by SQLParser#tableUnique.
    def exitTableUnique(self, ctx:SQLParser.TableUniqueContext):
        pass


    # Enter a parse tree produced by SQLParser#tableFk.
    def enterTableFk(self, ctx:SQLParser.TableFkContext):
        pass

    # Exit a parse tree produced by SQLParser#tableFk.
    def exitTableFk(self, ctx:SQLParser.TableFkContext):
        pass


    # Enter a parse tree produced by SQLParser#dropTable.
    def enterDropTable(self, ctx:SQLParser.DropTableContext):
        pass

    # Exit a parse tree produced by SQLParser#dropTable.
    def exitDropTable(self, ctx:SQLParser.DropTableContext):
        pass


    # Enter a parse tree produced by SQLParser#createIndex.
    def enterCreateIndex(self, ctx:SQLParser.CreateIndexContext):
        pass

    # Exit a parse tree produced by SQLParser#createIndex.
    def exitCreateIndex(self, ctx:SQLParser.CreateIndexContext):
        pass


    # Enter a parse tree produced by SQLParser#dropIndex.
    def enterDropIndex(self, ctx:SQLParser.DropIndexContext):
        pass

    # Exit a parse tree produced by SQLParser#dropIndex.
    def exitDropIndex(self, ctx:SQLParser.DropIndexContext):
        pass


    # Enter a parse tree produced by SQLParser#insertStmt.
    def enterInsertStmt(self, ctx:SQLParser.InsertStmtContext):
        pass

    # Exit a parse tree produced by SQLParser#insertStmt.
    def exitInsertStmt(self, ctx:SQLParser.InsertStmtContext):
        pass


    # Enter a parse tree produced by SQLParser#valuesRow.
    def enterValuesRow(self, ctx:SQLParser.ValuesRowContext):
        pass

    # Exit a parse tree produced by SQLParser#valuesRow.
    def exitValuesRow(self, ctx:SQLParser.ValuesRowContext):
        pass


    # Enter a parse tree produced by SQLParser#updateStmt.
    def enterUpdateStmt(self, ctx:SQLParser.UpdateStmtContext):
        pass

    # Exit a parse tree produced by SQLParser#updateStmt.
    def exitUpdateStmt(self, ctx:SQLParser.UpdateStmtContext):
        pass


    # Enter a parse tree produced by SQLParser#assignment.
    def enterAssignment(self, ctx:SQLParser.AssignmentContext):
        pass

    # Exit a parse tree produced by SQLParser#assignment.
    def exitAssignment(self, ctx:SQLParser.AssignmentContext):
        pass


    # Enter a parse tree produced by SQLParser#deleteStmt.
    def enterDeleteStmt(self, ctx:SQLParser.DeleteStmtContext):
        pass

    # Exit a parse tree produced by SQLParser#deleteStmt.
    def exitDeleteStmt(self, ctx:SQLParser.DeleteStmtContext):
        pass


    # Enter a parse tree produced by SQLParser#selectStmt.
    def enterSelectStmt(self, ctx:SQLParser.SelectStmtContext):
        pass

    # Exit a parse tree produced by SQLParser#selectStmt.
    def exitSelectStmt(self, ctx:SQLParser.SelectStmtContext):
        pass


    # Enter a parse tree produced by SQLParser#selectAll.
    def enterSelectAll(self, ctx:SQLParser.SelectAllContext):
        pass

    # Exit a parse tree produced by SQLParser#selectAll.
    def exitSelectAll(self, ctx:SQLParser.SelectAllContext):
        pass


    # Enter a parse tree produced by SQLParser#selectTableAll.
    def enterSelectTableAll(self, ctx:SQLParser.SelectTableAllContext):
        pass

    # Exit a parse tree produced by SQLParser#selectTableAll.
    def exitSelectTableAll(self, ctx:SQLParser.SelectTableAllContext):
        pass


    # Enter a parse tree produced by SQLParser#selectExpr.
    def enterSelectExpr(self, ctx:SQLParser.SelectExprContext):
        pass

    # Exit a parse tree produced by SQLParser#selectExpr.
    def exitSelectExpr(self, ctx:SQLParser.SelectExprContext):
        pass


    # Enter a parse tree produced by SQLParser#fromClause.
    def enterFromClause(self, ctx:SQLParser.FromClauseContext):
        pass

    # Exit a parse tree produced by SQLParser#fromClause.
    def exitFromClause(self, ctx:SQLParser.FromClauseContext):
        pass


    # Enter a parse tree produced by SQLParser#crossItem.
    def enterCrossItem(self, ctx:SQLParser.CrossItemContext):
        pass

    # Exit a parse tree produced by SQLParser#crossItem.
    def exitCrossItem(self, ctx:SQLParser.CrossItemContext):
        pass


    # Enter a parse tree produced by SQLParser#crossJoinItem.
    def enterCrossJoinItem(self, ctx:SQLParser.CrossJoinItemContext):
        pass

    # Exit a parse tree produced by SQLParser#crossJoinItem.
    def exitCrossJoinItem(self, ctx:SQLParser.CrossJoinItemContext):
        pass


    # Enter a parse tree produced by SQLParser#joinItem.
    def enterJoinItem(self, ctx:SQLParser.JoinItemContext):
        pass

    # Exit a parse tree produced by SQLParser#joinItem.
    def exitJoinItem(self, ctx:SQLParser.JoinItemContext):
        pass


    # Enter a parse tree produced by SQLParser#joinType.
    def enterJoinType(self, ctx:SQLParser.JoinTypeContext):
        pass

    # Exit a parse tree produced by SQLParser#joinType.
    def exitJoinType(self, ctx:SQLParser.JoinTypeContext):
        pass


    # Enter a parse tree produced by SQLParser#tableRef.
    def enterTableRef(self, ctx:SQLParser.TableRefContext):
        pass

    # Exit a parse tree produced by SQLParser#tableRef.
    def exitTableRef(self, ctx:SQLParser.TableRefContext):
        pass


    # Enter a parse tree produced by SQLParser#whereClause.
    def enterWhereClause(self, ctx:SQLParser.WhereClauseContext):
        pass

    # Exit a parse tree produced by SQLParser#whereClause.
    def exitWhereClause(self, ctx:SQLParser.WhereClauseContext):
        pass


    # Enter a parse tree produced by SQLParser#groupByClause.
    def enterGroupByClause(self, ctx:SQLParser.GroupByClauseContext):
        pass

    # Exit a parse tree produced by SQLParser#groupByClause.
    def exitGroupByClause(self, ctx:SQLParser.GroupByClauseContext):
        pass


    # Enter a parse tree produced by SQLParser#havingClause.
    def enterHavingClause(self, ctx:SQLParser.HavingClauseContext):
        pass

    # Exit a parse tree produced by SQLParser#havingClause.
    def exitHavingClause(self, ctx:SQLParser.HavingClauseContext):
        pass


    # Enter a parse tree produced by SQLParser#orderByClause.
    def enterOrderByClause(self, ctx:SQLParser.OrderByClauseContext):
        pass

    # Exit a parse tree produced by SQLParser#orderByClause.
    def exitOrderByClause(self, ctx:SQLParser.OrderByClauseContext):
        pass


    # Enter a parse tree produced by SQLParser#orderItem.
    def enterOrderItem(self, ctx:SQLParser.OrderItemContext):
        pass

    # Exit a parse tree produced by SQLParser#orderItem.
    def exitOrderItem(self, ctx:SQLParser.OrderItemContext):
        pass


    # Enter a parse tree produced by SQLParser#limitClause.
    def enterLimitClause(self, ctx:SQLParser.LimitClauseContext):
        pass

    # Exit a parse tree produced by SQLParser#limitClause.
    def exitLimitClause(self, ctx:SQLParser.LimitClauseContext):
        pass


    # Enter a parse tree produced by SQLParser#predicateExpr.
    def enterPredicateExpr(self, ctx:SQLParser.PredicateExprContext):
        pass

    # Exit a parse tree produced by SQLParser#predicateExpr.
    def exitPredicateExpr(self, ctx:SQLParser.PredicateExprContext):
        pass


    # Enter a parse tree produced by SQLParser#notExpr.
    def enterNotExpr(self, ctx:SQLParser.NotExprContext):
        pass

    # Exit a parse tree produced by SQLParser#notExpr.
    def exitNotExpr(self, ctx:SQLParser.NotExprContext):
        pass


    # Enter a parse tree produced by SQLParser#orExpr.
    def enterOrExpr(self, ctx:SQLParser.OrExprContext):
        pass

    # Exit a parse tree produced by SQLParser#orExpr.
    def exitOrExpr(self, ctx:SQLParser.OrExprContext):
        pass


    # Enter a parse tree produced by SQLParser#andExpr.
    def enterAndExpr(self, ctx:SQLParser.AndExprContext):
        pass

    # Exit a parse tree produced by SQLParser#andExpr.
    def exitAndExpr(self, ctx:SQLParser.AndExprContext):
        pass


    # Enter a parse tree produced by SQLParser#comparePred.
    def enterComparePred(self, ctx:SQLParser.ComparePredContext):
        pass

    # Exit a parse tree produced by SQLParser#comparePred.
    def exitComparePred(self, ctx:SQLParser.ComparePredContext):
        pass


    # Enter a parse tree produced by SQLParser#isNullPred.
    def enterIsNullPred(self, ctx:SQLParser.IsNullPredContext):
        pass

    # Exit a parse tree produced by SQLParser#isNullPred.
    def exitIsNullPred(self, ctx:SQLParser.IsNullPredContext):
        pass


    # Enter a parse tree produced by SQLParser#betweenPred.
    def enterBetweenPred(self, ctx:SQLParser.BetweenPredContext):
        pass

    # Exit a parse tree produced by SQLParser#betweenPred.
    def exitBetweenPred(self, ctx:SQLParser.BetweenPredContext):
        pass


    # Enter a parse tree produced by SQLParser#likePred.
    def enterLikePred(self, ctx:SQLParser.LikePredContext):
        pass

    # Exit a parse tree produced by SQLParser#likePred.
    def exitLikePred(self, ctx:SQLParser.LikePredContext):
        pass


    # Enter a parse tree produced by SQLParser#inSubqueryPred.
    def enterInSubqueryPred(self, ctx:SQLParser.InSubqueryPredContext):
        pass

    # Exit a parse tree produced by SQLParser#inSubqueryPred.
    def exitInSubqueryPred(self, ctx:SQLParser.InSubqueryPredContext):
        pass


    # Enter a parse tree produced by SQLParser#inListPred.
    def enterInListPred(self, ctx:SQLParser.InListPredContext):
        pass

    # Exit a parse tree produced by SQLParser#inListPred.
    def exitInListPred(self, ctx:SQLParser.InListPredContext):
        pass


    # Enter a parse tree produced by SQLParser#existsPred.
    def enterExistsPred(self, ctx:SQLParser.ExistsPredContext):
        pass

    # Exit a parse tree produced by SQLParser#existsPred.
    def exitExistsPred(self, ctx:SQLParser.ExistsPredContext):
        pass


    # Enter a parse tree produced by SQLParser#valuePred.
    def enterValuePred(self, ctx:SQLParser.ValuePredContext):
        pass

    # Exit a parse tree produced by SQLParser#valuePred.
    def exitValuePred(self, ctx:SQLParser.ValuePredContext):
        pass


    # Enter a parse tree produced by SQLParser#primaryValue.
    def enterPrimaryValue(self, ctx:SQLParser.PrimaryValueContext):
        pass

    # Exit a parse tree produced by SQLParser#primaryValue.
    def exitPrimaryValue(self, ctx:SQLParser.PrimaryValueContext):
        pass


    # Enter a parse tree produced by SQLParser#concatValue.
    def enterConcatValue(self, ctx:SQLParser.ConcatValueContext):
        pass

    # Exit a parse tree produced by SQLParser#concatValue.
    def exitConcatValue(self, ctx:SQLParser.ConcatValueContext):
        pass


    # Enter a parse tree produced by SQLParser#mulValue.
    def enterMulValue(self, ctx:SQLParser.MulValueContext):
        pass

    # Exit a parse tree produced by SQLParser#mulValue.
    def exitMulValue(self, ctx:SQLParser.MulValueContext):
        pass


    # Enter a parse tree produced by SQLParser#unaryValue.
    def enterUnaryValue(self, ctx:SQLParser.UnaryValueContext):
        pass

    # Exit a parse tree produced by SQLParser#unaryValue.
    def exitUnaryValue(self, ctx:SQLParser.UnaryValueContext):
        pass


    # Enter a parse tree produced by SQLParser#addValue.
    def enterAddValue(self, ctx:SQLParser.AddValueContext):
        pass

    # Exit a parse tree produced by SQLParser#addValue.
    def exitAddValue(self, ctx:SQLParser.AddValueContext):
        pass


    # Enter a parse tree produced by SQLParser#subqueryPrimary.
    def enterSubqueryPrimary(self, ctx:SQLParser.SubqueryPrimaryContext):
        pass

    # Exit a parse tree produced by SQLParser#subqueryPrimary.
    def exitSubqueryPrimary(self, ctx:SQLParser.SubqueryPrimaryContext):
        pass


    # Enter a parse tree produced by SQLParser#parenPrimary.
    def enterParenPrimary(self, ctx:SQLParser.ParenPrimaryContext):
        pass

    # Exit a parse tree produced by SQLParser#parenPrimary.
    def exitParenPrimary(self, ctx:SQLParser.ParenPrimaryContext):
        pass


    # Enter a parse tree produced by SQLParser#aggregatePrimary.
    def enterAggregatePrimary(self, ctx:SQLParser.AggregatePrimaryContext):
        pass

    # Exit a parse tree produced by SQLParser#aggregatePrimary.
    def exitAggregatePrimary(self, ctx:SQLParser.AggregatePrimaryContext):
        pass


    # Enter a parse tree produced by SQLParser#literalPrimary.
    def enterLiteralPrimary(self, ctx:SQLParser.LiteralPrimaryContext):
        pass

    # Exit a parse tree produced by SQLParser#literalPrimary.
    def exitLiteralPrimary(self, ctx:SQLParser.LiteralPrimaryContext):
        pass


    # Enter a parse tree produced by SQLParser#columnPrimary.
    def enterColumnPrimary(self, ctx:SQLParser.ColumnPrimaryContext):
        pass

    # Exit a parse tree produced by SQLParser#columnPrimary.
    def exitColumnPrimary(self, ctx:SQLParser.ColumnPrimaryContext):
        pass


    # Enter a parse tree produced by SQLParser#countStar.
    def enterCountStar(self, ctx:SQLParser.CountStarContext):
        pass

    # Exit a parse tree produced by SQLParser#countStar.
    def exitCountStar(self, ctx:SQLParser.CountStarContext):
        pass


    # Enter a parse tree produced by SQLParser#aggregateCall.
    def enterAggregateCall(self, ctx:SQLParser.AggregateCallContext):
        pass

    # Exit a parse tree produced by SQLParser#aggregateCall.
    def exitAggregateCall(self, ctx:SQLParser.AggregateCallContext):
        pass


    # Enter a parse tree produced by SQLParser#columnRef.
    def enterColumnRef(self, ctx:SQLParser.ColumnRefContext):
        pass

    # Exit a parse tree produced by SQLParser#columnRef.
    def exitColumnRef(self, ctx:SQLParser.ColumnRefContext):
        pass


    # Enter a parse tree produced by SQLParser#signedLiteral.
    def enterSignedLiteral(self, ctx:SQLParser.SignedLiteralContext):
        pass

    # Exit a parse tree produced by SQLParser#signedLiteral.
    def exitSignedLiteral(self, ctx:SQLParser.SignedLiteralContext):
        pass


    # Enter a parse tree produced by SQLParser#intLiteral.
    def enterIntLiteral(self, ctx:SQLParser.IntLiteralContext):
        pass

    # Exit a parse tree produced by SQLParser#intLiteral.
    def exitIntLiteral(self, ctx:SQLParser.IntLiteralContext):
        pass


    # Enter a parse tree produced by SQLParser#floatLiteral.
    def enterFloatLiteral(self, ctx:SQLParser.FloatLiteralContext):
        pass

    # Exit a parse tree produced by SQLParser#floatLiteral.
    def exitFloatLiteral(self, ctx:SQLParser.FloatLiteralContext):
        pass


    # Enter a parse tree produced by SQLParser#stringLiteral.
    def enterStringLiteral(self, ctx:SQLParser.StringLiteralContext):
        pass

    # Exit a parse tree produced by SQLParser#stringLiteral.
    def exitStringLiteral(self, ctx:SQLParser.StringLiteralContext):
        pass


    # Enter a parse tree produced by SQLParser#dateLiteral.
    def enterDateLiteral(self, ctx:SQLParser.DateLiteralContext):
        pass

    # Exit a parse tree produced by SQLParser#dateLiteral.
    def exitDateLiteral(self, ctx:SQLParser.DateLiteralContext):
        pass


    # Enter a parse tree produced by SQLParser#boolLiteral.
    def enterBoolLiteral(self, ctx:SQLParser.BoolLiteralContext):
        pass

    # Exit a parse tree produced by SQLParser#boolLiteral.
    def exitBoolLiteral(self, ctx:SQLParser.BoolLiteralContext):
        pass


    # Enter a parse tree produced by SQLParser#nullLiteral.
    def enterNullLiteral(self, ctx:SQLParser.NullLiteralContext):
        pass

    # Exit a parse tree produced by SQLParser#nullLiteral.
    def exitNullLiteral(self, ctx:SQLParser.NullLiteralContext):
        pass


    # Enter a parse tree produced by SQLParser#identifierList.
    def enterIdentifierList(self, ctx:SQLParser.IdentifierListContext):
        pass

    # Exit a parse tree produced by SQLParser#identifierList.
    def exitIdentifierList(self, ctx:SQLParser.IdentifierListContext):
        pass


    # Enter a parse tree produced by SQLParser#identifier.
    def enterIdentifier(self, ctx:SQLParser.IdentifierContext):
        pass

    # Exit a parse tree produced by SQLParser#identifier.
    def exitIdentifier(self, ctx:SQLParser.IdentifierContext):
        pass



del SQLParser