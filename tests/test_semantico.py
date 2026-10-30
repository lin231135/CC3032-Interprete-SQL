"""Fase 3: analisis semantico (contra el catalogo) y anotaciones del AST."""

from arbol import nodes as n
from driver import analizar
from tests.helpers import bd, categorias


def test_errores_con_ubicacion(tmp_path):
    db = bd(tmp_path, universidad=True)
    r = analizar("SELECT nombre\nFROM estudiantes\nWHERE apellido = 1;", db)
    e = r.errores_semanticos[0]
    assert (e.line, e.column, e.category, e.fase) == (3, 7, "columna", "semantico")


def test_se_reportan_todos_los_errores_y_no_se_ejecuta_nada(tmp_path):
    db = bd(tmp_path, universidad=True)
    r = analizar("DELETE FROM cursos; SELECT x FROM fantasma; SELECT nombre + 1 FROM cursos;", db, ejecutar=True)
    assert {e.category for e in r.errores} == {"tabla", "tipo"}
    assert not r.ejecutado
    assert db.contar("cursos") == 5


def test_catalogo_simulado_no_toca_el_disco(tmp_path):
    db = bd(tmp_path)
    r = analizar("CREATE TABLE t (a INT); INSERT INTO t VALUES (1); SELECT a FROM t;", db)
    assert r.ok and db.catalogo.tabla("t") is None


def test_resolucion_de_columnas_y_tipos(tmp_path):
    db = bd(tmp_path, universidad=True)
    r = analizar("SELECT e.nombre, nota FROM estudiantes e JOIN inscripciones i ON i.estudiante_id = e.id;", db)
    sel = r.ast.sentencias[0]
    nota = sel.items[1].expr
    assert (nota.ref_alias, nota.ref_nivel) == ("i", 0)
    assert [str(c.tipo) for c in sel.columnas_salida] == ["VARCHAR(50)", "FLOAT"]


def test_subconsulta_correlacionada_se_marca(tmp_path):
    db = bd(tmp_path, universidad=True)
    r = analizar("SELECT nombre FROM estudiantes e WHERE EXISTS (SELECT 1 FROM inscripciones i "
                 "WHERE i.estudiante_id = e.id) AND id IN (SELECT estudiante_id FROM inscripciones);", db)
    w = r.ast.sentencias[0].where
    assert w.izquierda.consulta.correlacionada
    assert not w.derecha.consulta.correlacionada
    ref = w.izquierda.consulta.where.derecha
    assert (ref.ref_alias, ref.ref_nivel) == ("e", 1)


def test_texto_comparado_con_date_se_convierte(tmp_path):
    db = bd(tmp_path, universidad=True)
    r = analizar("SELECT nombre FROM estudiantes WHERE ingreso > '2023-01-01';", db)
    lit = r.ast.sentencias[0].where.derecha
    assert isinstance(lit, n.Literal) and str(lit.tipo_literal) == "DATE"


def test_categorias_principales(tmp_path):
    db = bd(tmp_path, universidad=True)
    assert categorias(None, "SELECT * FROM t;") == {"tabla"}
    assert "referencia" in categorias(None, "CREATE TABLE a (x INT); CREATE TABLE b (x INT); SELECT x FROM a, b;")
    assert categorias(None, "DROP INDEX i;") == {"indice"}
    assert "subconsulta" in categorias(None, "CREATE TABLE a (x INT, y INT); SELECT (SELECT x, y FROM a);")
    assert "agregacion" in categorias(None, "CREATE TABLE a (x INT); SELECT x FROM a WHERE SUM(x) > 1;")
    assert "valor" in categorias(None, "CREATE TABLE a (x INT NOT NULL); INSERT INTO a VALUES (NULL);")
    assert categorias(db, "SELECT nombre FROM estudiantes WHERE edad = (SELECT edad FROM estudiantes);") == \
        {"subconsulta"}
