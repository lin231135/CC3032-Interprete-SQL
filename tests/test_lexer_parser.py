"""Fase 1: tokens, arbol sintactico y errores lexicos/sintacticos."""

from driver import analizar


def test_tokens_con_tipo_lexema_y_posicion():
    r = analizar("select nombre\nFROM t WHERE x >= 1.5;")
    tipos = [(t.tipo, t.lexema) for t in r.tokens]
    assert tipos[:3] == [("SELECT", "select"), ("IDENTIFIER", "nombre"), ("FROM", "FROM")]
    assert ("GTE", ">=") in tipos and ("FLOAT_LIT", "1.5") in tipos
    desde = r.tokens[2]
    assert (desde.linea, desde.columna) == (2, 1)


def test_comentarios_y_espacios_no_son_tokens():
    r = analizar("-- hola\nSELECT /* x */ 1;")
    assert [t.tipo for t in r.tokens] == ["SELECT", "INT_LIT", "SEMI"]


def test_operadores_diferente():
    r = analizar("SELECT 1 <> 2, 1 != 2;")
    assert [t.lexema for t in r.tokens if t.tipo == "NEQ"] == ["<>", "!="]


def test_error_lexico_con_ubicacion():
    r = analizar("SELECT 1;\nSELECT @;")
    assert r.errores_lexicos
    e = r.errores_lexicos[0]
    assert (e.line, e.column, e.fase) == (2, 8, "lexico")
    assert "@" in e.message


def test_error_sintactico_en_espanol():
    r = analizar("SELECT nombre FROM WHERE x = 1;")
    assert r.errores_sintacticos
    e = r.errores_sintacticos[0]
    assert e.fase == "sintactico" and e.line == 1
    assert "esperaba" in e.message or "inválida" in e.message


def test_con_errores_sintacticos_no_hay_ast():
    r = analizar("SELECT FROM;")
    assert r.tree is not None and r.ast is None


def test_arbol_sintactico_usa_las_reglas_de_la_gramatica():
    r = analizar("SELECT a FROM t;")
    texto = r.tree.toStringTree(recog=r.parser)
    assert texto.startswith("(script (statement (selectStmt")
