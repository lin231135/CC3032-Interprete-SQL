"""Fase 2: construccion del AST (ASTBuilder) y su dibujo en texto."""

import datetime

from arbol import nodes as n
from arbol.render import ast_texto
from driver import analizar


def ast(sql: str) -> n.Script:
    r = analizar(sql)
    assert r.ast is not None, [str(e) for e in r.errores]
    return r.ast


def test_select_completo():
    s = ast("SELECT DISTINCT e.nombre AS n FROM estudiantes e JOIN cursos c ON c.id = e.id "
            "WHERE e.edad >= 18 GROUP BY e.nombre HAVING COUNT(*) > 1 ORDER BY n DESC LIMIT 3 OFFSET 1;").sentencias[0]
    assert isinstance(s, n.Select) and s.distinct
    assert s.items[0].alias == "n"
    assert [(f.tabla, f.alias, f.union) for f in s.desde] == [("estudiantes", "e", "BASE"), ("cursos", "c", "INNER")]
    assert isinstance(s.where, n.BinaryOp) and s.where.op == ">="
    assert isinstance(s.having.izquierda, n.Aggregate) and s.having.izquierda.argumento is None
    assert s.order_by[0].descendente and (s.limit, s.offset) == (3, 1)


def test_precedencia_and_or_not():
    w = ast("SELECT 1 FROM t WHERE NOT a = 1 AND b = 2 OR c = 3;").sentencias[0].where
    assert w.op == "OR"
    assert w.izquierda.op == "AND"
    assert isinstance(w.izquierda.izquierda, n.UnaryOp) and w.izquierda.izquierda.op == "NOT"


def test_precedencia_aritmetica():
    e = ast("SELECT 1 + 2 * 3;").sentencias[0].items[0].expr
    assert e.op == "+" and e.derecha.op == "*"


def test_literales_y_normalizacion():
    fila = ast("INSERT INTO T VALUES (-5, 2.5, 'it''s', TRUE, NULL, DATE '2024-01-02');").sentencias[0].filas[0]
    assert [x.valor for x in fila] == [-5, 2.5, "it's", True, None, datetime.date(2024, 1, 2)]
    assert ast("SELECT Nombre FROM ESTUDIANTES;").sentencias[0].desde[0].tabla == "estudiantes"


def test_not_exists_y_not_in():
    w = ast("SELECT 1 FROM t WHERE NOT EXISTS (SELECT 1 FROM u) AND x NOT IN (1, 2);").sentencias[0].where
    assert isinstance(w.izquierda, n.Exists) and w.izquierda.negado
    assert isinstance(w.derecha, n.InList) and w.derecha.negado


def test_create_table_con_restricciones():
    s = ast("CREATE TABLE t (id INT PRIMARY KEY, n VARCHAR(10) NOT NULL UNIQUE DEFAULT 'x', "
            "c INT REFERENCES cursos(id), FOREIGN KEY (n) REFERENCES u(m));").sentencias[0]
    assert s.columnas[0].primary_key and s.columnas[0].not_null
    assert str(s.columnas[1].tipo_dato) == "VARCHAR(10)" and s.columnas[1].unique
    assert s.columnas[1].default.valor == "x"
    assert [(f.columna_local, f.tabla_ref, f.columna_ref) for f in s.foraneas] == \
        [("c", "cursos", "id"), ("n", "u", "m")]


def test_texto_original_de_la_sentencia():
    s = ast("SELECT   a\nFROM t;").sentencias[0]
    assert s.texto == "SELECT   a\nFROM t"


def test_ast_en_texto():
    texto = ast_texto(ast("SELECT a FROM t WHERE a > 1;"))
    assert "Select" in texto and "where: BinaryOp" in texto and "op: >" in texto
