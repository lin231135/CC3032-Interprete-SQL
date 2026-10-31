"""
Parametriza pruebas/runner.ejecutar_bateria() con pytest: un test por
archivo .sql de la bateria, mas un chequeo de que los scripts de
pruebas/demo/ corren en orden sobre una base nueva.
"""

import pytest

from driver import analizar_archivo
from pruebas.runner import RAIZ, ejecutar_bateria
from tests.helpers import bd

RESULTADOS = ejecutar_bateria()


@pytest.mark.parametrize(
    "resultado",
    RESULTADOS,
    ids=[str(r.archivo.relative_to(RAIZ)) for r in RESULTADOS],
)
def test_bateria(resultado):
    assert resultado.paso, resultado.razon


def test_hay_casos_validos_e_invalidos_en_cada_categoria():
    categorias = {r.archivo.parent.parent.name for r in RESULTADOS}
    for cat in categorias:
        tipos = {r.es_valido for r in RESULTADOS if r.archivo.parent.parent.name == cat}
        assert tipos == {True, False}, cat


def test_demos_en_orden(tmp_path):
    """Los demos se corren en orden sobre la misma base; el de errores debe reportarlos."""
    db = bd(tmp_path)
    demos = sorted((RAIZ / "demo").glob("*.sql"))
    assert demos
    for ruta in demos:
        r = analizar_archivo(ruta, db, ejecutar=True)
        if "errores" in ruta.name:
            assert r.errores, ruta.name
        else:
            assert not r.errores, (ruta.name, [str(e) for e in r.errores])
