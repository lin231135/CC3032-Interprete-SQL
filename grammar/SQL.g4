// Gramatica del subconjunto de SQL que acepta el interprete.
//
// Palabras reservadas sin distincion de mayusculas (caseInsensitive). Los
// identificadores se normalizan a minusculas en el ASTBuilder.
//
// Precedencia de expresiones (de menor a mayor):
//   OR  <  AND  <  NOT  <  predicados (=, <, IS NULL, BETWEEN, LIKE, IN, EXISTS)
//   <  ||  <  + -  <  * / %  <  - unario  <  primarios
//
// Regenerar el parser: python build_grammar.py

grammar SQL;

options { caseInsensitive = true; }

// ---------------------------------------------------------------------------
// Script y sentencias
// ---------------------------------------------------------------------------

script
    : SEMI* (statement (SEMI+ statement)* SEMI*)? EOF
    ;

statement
    : createTable
    | dropTable
    | createIndex
    | dropIndex
    | insertStmt
    | updateStmt
    | deleteStmt
    | selectStmt
    ;

// --- DDL -------------------------------------------------------------------

createTable
    : CREATE TABLE (IF NOT EXISTS)? identifier LPAREN tableElement (COMMA tableElement)* RPAREN
    ;

tableElement
    : columnDef
    | tableConstraint
    ;

columnDef
    : identifier dataType columnConstraint*
    ;

dataType
    : (INT | INTEGER)                    # intType
    | FLOAT                              # floatType
    | VARCHAR LPAREN INT_LIT RPAREN      # varcharType
    | BOOLEAN                            # booleanType
    | DATE                               # dateType
    ;

columnConstraint
    : PRIMARY KEY                                           # pkConstraint
    | NOT NULL                                              # notNullConstraint
    | NULL                                                  # nullConstraint
    | UNIQUE                                                # uniqueConstraint
    | DEFAULT signedLiteral                                 # defaultConstraint
    | REFERENCES identifier LPAREN identifier RPAREN        # referencesConstraint
    ;

tableConstraint
    : PRIMARY KEY LPAREN identifierList RPAREN                                          # tablePk
    | UNIQUE LPAREN identifierList RPAREN                                               # tableUnique
    | FOREIGN KEY LPAREN identifier RPAREN REFERENCES identifier LPAREN identifier RPAREN  # tableFk
    ;

dropTable
    : DROP TABLE (IF EXISTS)? identifier
    ;

createIndex
    : CREATE UNIQUE? INDEX identifier ON identifier LPAREN identifier RPAREN
    ;

dropIndex
    : DROP INDEX (IF EXISTS)? identifier
    ;

// --- DML -------------------------------------------------------------------

insertStmt
    : INSERT INTO identifier (LPAREN identifierList RPAREN)? (VALUES valuesRow (COMMA valuesRow)* | selectStmt)
    ;

valuesRow
    : LPAREN expr (COMMA expr)* RPAREN
    ;

updateStmt
    : UPDATE identifier SET assignment (COMMA assignment)* whereClause?
    ;

assignment
    : identifier EQ expr
    ;

deleteStmt
    : DELETE FROM identifier whereClause?
    ;

// --- SELECT ----------------------------------------------------------------

selectStmt
    : SELECT DISTINCT? selectItem (COMMA selectItem)*
      fromClause?
      whereClause?
      groupByClause?
      havingClause?
      orderByClause?
      limitClause?
    ;

selectItem
    : STAR                              # selectAll
    | identifier DOT STAR               # selectTableAll
    | expr (AS? identifier)?            # selectExpr
    ;

fromClause
    : FROM tableRef fromExtra*
    ;

fromExtra
    : COMMA tableRef                    # crossItem
    | CROSS JOIN tableRef               # crossJoinItem
    | joinType? JOIN tableRef ON expr   # joinItem
    ;

joinType
    : INNER
    | LEFT OUTER?
    ;

tableRef
    : identifier (AS? identifier)?
    ;

whereClause
    : WHERE expr
    ;

groupByClause
    : GROUP BY expr (COMMA expr)*
    ;

havingClause
    : HAVING expr
    ;

orderByClause
    : ORDER BY orderItem (COMMA orderItem)*
    ;

orderItem
    : expr (ASC | DESC)?
    ;

limitClause
    : LIMIT INT_LIT (OFFSET INT_LIT)?
    ;

// ---------------------------------------------------------------------------
// Expresiones
// ---------------------------------------------------------------------------

expr
    : NOT expr                  # notExpr
    | expr AND expr             # andExpr
    | expr OR expr              # orExpr
    | predicate                 # predicateExpr
    ;

predicate
    : valueExpr op=(EQ | NEQ | LT | LTE | GT | GTE) valueExpr                 # comparePred
    | valueExpr IS NOT? NULL                                                  # isNullPred
    | valueExpr NOT? BETWEEN valueExpr AND valueExpr                          # betweenPred
    | valueExpr NOT? LIKE valueExpr                                           # likePred
    | valueExpr NOT? IN LPAREN selectStmt RPAREN                              # inSubqueryPred
    | valueExpr NOT? IN LPAREN valueExpr (COMMA valueExpr)* RPAREN            # inListPred
    | EXISTS LPAREN selectStmt RPAREN                                         # existsPred
    | valueExpr                                                               # valuePred
    ;

valueExpr
    : op=(MINUS | PLUS) valueExpr                         # unaryValue
    | valueExpr op=(STAR | SLASH | PERCENT) valueExpr     # mulValue
    | valueExpr op=(PLUS | MINUS) valueExpr               # addValue
    | valueExpr CONCAT valueExpr                          # concatValue
    | primary                                             # primaryValue
    ;

primary
    : LPAREN selectStmt RPAREN      # subqueryPrimary
    | LPAREN expr RPAREN            # parenPrimary
    | aggregate                     # aggregatePrimary
    | literal                       # literalPrimary
    | columnRef                     # columnPrimary
    ;

aggregate
    : COUNT LPAREN STAR RPAREN                                          # countStar
    | func=(COUNT | SUM | AVG | MIN | MAX) LPAREN DISTINCT? expr RPAREN  # aggregateCall
    ;

columnRef
    : identifier (DOT identifier)?
    ;

signedLiteral
    : MINUS? literal
    ;

literal
    : INT_LIT                   # intLiteral
    | FLOAT_LIT                 # floatLiteral
    | STRING_LIT                # stringLiteral
    | DATE STRING_LIT           # dateLiteral
    | (TRUE | FALSE)            # boolLiteral
    | NULL                      # nullLiteral
    ;

identifierList
    : identifier (COMMA identifier)*
    ;

identifier
    : IDENTIFIER
    ;

// ---------------------------------------------------------------------------
// Lexer
// ---------------------------------------------------------------------------

// palabras reservadas
SELECT      : 'SELECT';
DISTINCT    : 'DISTINCT';
FROM        : 'FROM';
WHERE       : 'WHERE';
GROUP       : 'GROUP';
BY          : 'BY';
HAVING      : 'HAVING';
ORDER       : 'ORDER';
ASC         : 'ASC';
DESC        : 'DESC';
LIMIT       : 'LIMIT';
OFFSET      : 'OFFSET';
AS          : 'AS';
JOIN        : 'JOIN';
INNER       : 'INNER';
LEFT        : 'LEFT';
OUTER       : 'OUTER';
CROSS       : 'CROSS';
ON          : 'ON';
AND         : 'AND';
OR          : 'OR';
NOT         : 'NOT';
IN          : 'IN';
EXISTS      : 'EXISTS';
BETWEEN     : 'BETWEEN';
LIKE        : 'LIKE';
IS          : 'IS';
NULL        : 'NULL';
TRUE        : 'TRUE';
FALSE       : 'FALSE';
INSERT      : 'INSERT';
INTO        : 'INTO';
VALUES      : 'VALUES';
UPDATE      : 'UPDATE';
SET         : 'SET';
DELETE      : 'DELETE';
CREATE      : 'CREATE';
DROP        : 'DROP';
TABLE       : 'TABLE';
INDEX       : 'INDEX';
UNIQUE      : 'UNIQUE';
PRIMARY     : 'PRIMARY';
KEY         : 'KEY';
FOREIGN     : 'FOREIGN';
REFERENCES  : 'REFERENCES';
DEFAULT     : 'DEFAULT';
IF          : 'IF';

// funciones de agregacion
COUNT       : 'COUNT';
SUM         : 'SUM';
AVG         : 'AVG';
MIN         : 'MIN';
MAX         : 'MAX';

// tipos de datos
INT         : 'INT';
INTEGER     : 'INTEGER';
FLOAT       : 'FLOAT';
VARCHAR     : 'VARCHAR';
BOOLEAN     : 'BOOLEAN';
DATE        : 'DATE';

// simbolos
LPAREN      : '(';
RPAREN      : ')';
COMMA       : ',';
SEMI        : ';';
DOT         : '.';
STAR        : '*';
PLUS        : '+';
MINUS       : '-';
SLASH       : '/';
PERCENT     : '%';
CONCAT      : '||';
EQ          : '=';
NEQ         : '<>' | '!=';
LTE         : '<=';
GTE         : '>=';
LT          : '<';
GT          : '>';

// literales
FLOAT_LIT   : [0-9]+ '.' [0-9]* | '.' [0-9]+;
INT_LIT     : [0-9]+;
STRING_LIT  : '\'' ( ~['\r\n] | '\'\'' )* '\'';

IDENTIFIER  : [A-Z_À-ÿ] [A-Z_0-9À-ÿ]*;

// ignorados
LINE_COMMENT  : '--' ~[\r\n]* -> skip;
BLOCK_COMMENT : '/*' .*? '*/' -> skip;
WS            : [ \t\r\n]+ -> skip;
