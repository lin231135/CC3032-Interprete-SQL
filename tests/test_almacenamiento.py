"""Formato de almacenamiento: metadata.txt, CSV e indices."""

import datetime

from almacenamiento.catalog import Catalog, Columna, Indice, LlaveForanea, Tabla
from almacenamiento.database import Database
from almacenamiento.indexes import ArchivoIndice
from core.types import DATE, INT, TipoSQL, deserializar, serializar
from tests.helpers import bd, ejecutar, filas


def test_metadata_ida_y_vuelta():
    cat = Catalog()
    cat.tablas["t"] = Tabla("t", [Columna("id", INT, True), Columna("s", TipoSQL("VARCHAR", 5), False, "it's"),
                                  Columna("d", DATE, False, datetime.date(2024, 1, 2)), Columna("x", INT, False, None)],
                            ["id"], [["s"]], [LlaveForanea("x", "t", "id")])
    cat.indices["i"] = Indice("i", "t", "s", True)
    texto = cat.a_texto()
    assert "COLUMNA s VARCHAR(5) NULL DEFAULT 'it''s'" in texto
    assert "INDICE UNICO i ON t (s)" in texto
    assert Catalog.desde_texto(texto) == cat


def test_serializacion_de_valores():
    for valor, tipo in [(None, INT), ("a\\b\nc", TipoSQL("VARCHAR", 9)), (datetime.date(2020, 2, 29), DATE)]:
        assert deserializar(serializar(valor), tipo) == valor
    assert serializar(None) == r"\N"


def test_los_datos_persisten_en_disco(tmp_path):
    db = bd(tmp_path, universidad=True)
    otra = Database(db.ruta)  # se vuelve a leer todo desde los archivos
    assert otra.catalogo.tabla("estudiantes").primary_key == ["id"]
    assert filas(otra, "SELECT COUNT(*) FROM inscripciones;") == [(13,)]
    lineas = (db.ruta / "estudiantes.csv").read_text(encoding="utf-8").splitlines()
    assert lineas[0] == "id,nombre,edad,carrera,activo,ingreso"
    assert lineas[7] == r"7,Gabriela Soto,16,Industrial,TRUE,\N"


def test_texto_con_coma_y_salto_de_linea_ocupa_una_linea(tmp_path):
    db = bd(tmp_path)
    ejecutar(db, "CREATE TABLE t (s VARCHAR(20)); INSERT INTO t VALUES ('a,b' || 'c');")
    db.insertar("t", [{"s": "x\ny"}])
    assert len((db.ruta / "t.csv").read_text(encoding="utf-8").splitlines()) == 3
    assert [f["s"] for f in db.leer_tabla("t")] == ["a,bc", "x\ny"]


def test_indice_busquedas_y_remapeo(tmp_path):
    idx = ArchivoIndice.construir(Indice("i", "t", "v"), INT, [10, 20, None, 20, 30])
    assert idx.buscar(20) == [1, 3] and idx.buscar(None) == []
    assert idx.buscar_rango(15, True, None, True) == [1, 3, 4]
    assert idx.buscar_rango(None, True, 20, False) == [0]
    idx.quitar(10, 0)
    idx.remapear([0])
    assert idx.buscar(20) == [0, 2] and idx.buscar(30) == [3]
    ruta = tmp_path / "i.idx"
    idx.guardar(ruta)
    assert ArchivoIndice.cargar(ruta, idx.definicion, INT).entradas == idx.entradas


def test_indice_se_reconstruye_si_falta_el_archivo(tmp_path):
    db = bd(tmp_path, universidad=True)
    ejecutar(db, "CREATE INDEX idx_edad ON estudiantes (edad);")
    db.ruta_indice("idx_edad").unlink()
    r = ejecutar(db, "SELECT nombre FROM estudiantes WHERE edad = 20;")
    assert r.ultima_consulta.filas == [("Ana López",)]
    assert db.ruta_indice("idx_edad").exists()


def test_leer_posiciones_solo_devuelve_las_pedidas(tmp_path):
    db = bd(tmp_path, universidad=True)
    assert [p for p, _ in db.leer_posiciones("estudiantes", [6, 1])] == [1, 6]
