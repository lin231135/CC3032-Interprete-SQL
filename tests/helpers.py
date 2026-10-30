"""Utilidades para las pruebas del interprete."""

from __future__ import annotations

from pathlib import Path

from almacenamiento.database import Database
from driver import Resultado, analizar

BASE_UNIVERSIDAD = Path(__file__).resolve().parent.parent / "pruebas" / "bases" / "universidad.sql"


def bd(tmp_path, universidad: bool = False) -> Database:
    db = Database(tmp_path / "bd")
    if universidad:
        ejecutar(db, BASE_UNIVERSIDAD.read_text(encoding="utf-8"))
    return db


def ejecutar(db: Database, sql: str) -> Resultado:
    """Ejecuta `sql` y exige que no haya errores."""
    r = analizar(sql, db, ejecutar=True)
    assert not r.errores, [str(e) for e in r.errores]
    return r


def filas(db: Database, sql: str) -> list[tuple]:
    """Filas del ultimo SELECT de `sql`."""
    return ejecutar(db, sql).ultima_consulta.filas


def categorias(db: Database | None, sql: str) -> set[str]:
    r = analizar(sql, db, ejecutar=db is not None)
    return {e.category for e in r.errores}
