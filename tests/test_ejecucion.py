"""Fase 4: interprete (atomicidad, restricciones, indices, resultados)."""

from driver import analizar
from tests.helpers import bd, ejecutar, filas


def test_sentencia_atomica_no_escribe_nada_si_falla(tmp_path):
    db = bd(tmp_path, universidad=True)
    r = analizar("INSERT INTO cursos VALUES (10, 'Nuevo', 1), (1, 'Repetido', 1);", db, ejecutar=True)
    assert r.errores_ejecucion and r.errores_ejecucion[0].category == "restriccion"
    assert db.contar("cursos") == 5


def test_el_script_se_detiene_en_el_error_y_lo_anterior_queda(tmp_path):
    db = bd(tmp_path, universidad=True)
    r = analizar("INSERT INTO cursos VALUES (10, 'Nuevo', 1);\n"
                 "INSERT INTO cursos VALUES (10, 'Otro', 1);\n"
                 "DELETE FROM inscripciones;", db, ejecutar=True)
    assert len(r.resultados) == 2 and r.resultados[0].ok and not r.resultados[1].ok
    assert r.errores_ejecucion[0].line == 2
    assert db.contar("cursos") == 6 and db.contar("inscripciones") == 13


def test_resultado_de_select(tmp_path):
    db = bd(tmp_path, universidad=True)
    res = ejecutar(db, "SELECT nombre, edad FROM estudiantes WHERE id = 1;").ultima_consulta
    assert res.columnas == ["nombre", "edad"] and res.tipos == ["VARCHAR(50)", "INT"]
    assert res.filas == [("Ana López", 20)]
    assert "Ana López" in res.como_tabla()


def test_mensajes_de_ddl_y_dml(tmp_path):
    db = bd(tmp_path, universidad=True)
    r = ejecutar(db, "UPDATE estudiantes SET edad = 30 WHERE carrera = 'Civil'; DELETE FROM inscripciones;")
    assert [x.afectadas for x in r.resultados] == [2, 13]
    assert "2 fila(s) actualizada(s)" in r.resultados[0].mensaje


def test_indice_da_el_mismo_resultado_que_el_recorrido(tmp_path):
    db = bd(tmp_path, universidad=True)
    consultas = ["SELECT id FROM estudiantes WHERE edad >= 18 AND edad < 22 ORDER BY id;",
                 "SELECT id FROM estudiantes WHERE edad BETWEEN 16 AND 19 ORDER BY id;",
                 "SELECT id FROM estudiantes WHERE edad IN (17, 25, 99) ORDER BY id;",
                 "SELECT id FROM estudiantes WHERE edad = 20;"]
    sin_indice = [filas(db, q) for q in consultas]
    ejecutar(db, "CREATE INDEX idx_edad ON estudiantes (edad);")
    for q, esperado in zip(consultas, sin_indice):
        r = ejecutar(db, q).ultima_consulta
        assert r.filas == esperado, q
        assert any("idx_edad" in p for p in r.plan), r.plan


def test_indice_se_mantiene_con_insert_update_delete(tmp_path):
    db = bd(tmp_path, universidad=True)
    ejecutar(db, "CREATE INDEX idx_edad ON estudiantes (edad);")
    ejecutar(db, "INSERT INTO estudiantes (id, nombre, edad) VALUES (9, 'Iván', 18), (10, 'Julia', 33);")
    ejecutar(db, "UPDATE estudiantes SET edad = 19 WHERE id = 1;")
    ejecutar(db, "DELETE FROM estudiantes WHERE id = 7;")
    reconstruido: dict[int, list[int]] = {}
    for pos, fila in enumerate(db.leer_tabla("estudiantes")):
        if fila["edad"] is not None:
            reconstruido.setdefault(fila["edad"], []).append(pos)
    assert db.indice("idx_edad").entradas == reconstruido


def test_left_join_rellena_con_null(tmp_path):
    db = bd(tmp_path, universidad=True)
    assert filas(db, "SELECT e.nombre, i.curso_id FROM estudiantes e LEFT JOIN inscripciones i "
                     "ON i.estudiante_id = e.id WHERE i.curso_id IS NULL;") == [("Gabriela Soto", None)]


def test_division_entre_cero_es_error_de_ejecucion(tmp_path):
    db = bd(tmp_path)
    r = analizar("SELECT 1 / 0;", db, ejecutar=True)
    assert [e.category for e in r.errores] == ["ejecucion"]
    assert r.errores[0].fase == "ejecucion"
