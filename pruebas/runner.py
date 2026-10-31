"""
Ejecuta la bateria de archivos .sql bajo pruebas/<categoria>/{validos,invalidos}/.

Lo usan tests/test_bateria.py (via pytest) y el boton "Bateria" del IDE.
Cada caso corre sobre una base de datos NUEVA en un directorio temporal.

Cabecera de cada archivo (comentarios `--` al inicio):
  -- @caso: descripcion                    (obligatoria)
  -- @usar: universidad                    (ejecuta antes pruebas/bases/universidad.sql; repetible)
  -- @error: categoria                     (invalidos; 1 o mas: lexico, sintactico, tabla, columna, tipo,
                                            valor, referencia, indice, subconsulta, agregacion, restriccion,
                                            ejecucion)
  -- @columnas: a, b                       (validos: columnas del ULTIMO SELECT)
  -- @filas: N                             (validos: cantidad de filas del ultimo SELECT)
  -- @resultado: v1, v2 | v3, v4           (validos: filas exactas del ultimo SELECT, en orden)
  -- @plan: texto                          (validos: el plan de alguna sentencia contiene el texto)
  -- @no_plan: texto                       (validos: ningun plan contiene el texto)
  -- @existe: ruta                         (validos: el archivo existe en la base al terminar)
  -- @no_existe: ruta
  -- @contiene: ruta :: texto              (validos: ese archivo de la base contiene el texto)

  - validos/   -> 0 errores (de analisis y de ejecucion) y se cumplen las directivas.
  - invalidos/ -> >= 1 error y TODAS las categorias de @error: aparecen.

`pruebas/demo/` y `pruebas/bases/` quedan fuera de `ejecutar_bateria()`.
"""

from __future__ import annotations

import re
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

# permite `python pruebas/runner.py` desde la raiz del repo
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from almacenamiento.database import Database
from core.types import formatear
from driver import analizar, analizar_archivo

RAIZ = Path(__file__).parent
BASES = RAIZ / "bases"


@dataclass
class ResultadoPrueba:
    archivo: Path
    es_valido: bool  # True si esta bajo .../validos/
    caso: str
    categorias_esperadas: list[str] = field(default_factory=list)
    paso: bool = False
    razon: str = ""

    def __str__(self) -> str:
        estado = "PASA" if self.paso else "FALLA"
        return f"[{estado}] {self.archivo.relative_to(RAIZ)} - {self.caso}"


@dataclass
class Cabecera:
    caso: str = ""
    usar: list[str] = field(default_factory=list)
    errores: list[str] = field(default_factory=list)
    columnas: list[str] | None = None
    filas: int | None = None
    resultado: list[list[str]] | None = None
    plan: list[str] = field(default_factory=list)
    no_plan: list[str] = field(default_factory=list)
    existe: list[str] = field(default_factory=list)
    no_existe: list[str] = field(default_factory=list)
    contiene: list[tuple[str, str]] = field(default_factory=list)


_RE_DIRECTIVA = re.compile(r"^\s*--\s*@(\w+):\s*(.*?)\s*$")


def _leer_cabecera(ruta: Path) -> Cabecera:
    cab = Cabecera()
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        m = _RE_DIRECTIVA.match(linea)
        if m:
            clave, valor = m.groups()
            if clave == "caso":
                cab.caso = valor
            elif clave == "usar":
                cab.usar.append(valor)
            elif clave == "error":
                cab.errores.append(valor.split()[0])
            elif clave == "columnas":
                cab.columnas = [x.strip() for x in valor.split(",")]
            elif clave == "filas":
                cab.filas = int(valor)
            elif clave == "resultado":
                cab.resultado = [[x.strip() for x in f.split(",")] for f in valor.split("|")] if valor else []
            elif clave in ("plan", "no_plan", "existe", "no_existe"):
                getattr(cab, clave).append(valor)
            elif clave == "contiene":
                archivo, _, texto = valor.partition("::")
                cab.contiene.append((archivo.strip(), texto.strip()))
            continue
        if linea.strip() and not linea.strip().startswith("--"):
            break  # termino la cabecera de comentarios
    return cab


def _evaluar(ruta: Path) -> ResultadoPrueba:
    es_valido = ruta.parent.name == "validos"
    cab = _leer_cabecera(ruta)

    def res(paso: bool, razon: str = "") -> ResultadoPrueba:
        return ResultadoPrueba(ruta, es_valido, cab.caso, cab.errores, paso, razon)

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        db = Database(Path(tmp) / "bd")
        for base in cab.usar:
            previo = analizar((BASES / f"{base}.sql").read_text(encoding="utf-8"), db, ejecutar=True)
            if previo.errores:
                return res(False, f"la base '{base}' falló: {[str(e) for e in previo.errores]}")
        resultado = analizar_archivo(ruta, db, ejecutar=True)

        if not es_valido:
            if not resultado.errores:
                return res(False, "se esperaba >=1 error, hubo 0")
            obtenidas = {e.category for e in resultado.errores}
            faltantes = [c for c in cab.errores if c not in obtenidas]
            if faltantes:
                return res(False, f"faltaron las categorias {faltantes} (se obtuvieron {sorted(obtenidas)}: "
                                  f"{[str(e) for e in resultado.errores]})")
            return res(True)

        if resultado.errores:
            return res(False, f"se esperaban 0 errores, hubo {len(resultado.errores)}: "
                              f"{[str(e) for e in resultado.errores]}")
        consulta = resultado.ultima_consulta
        if cab.columnas is not None or cab.filas is not None or cab.resultado is not None:
            if consulta is None:
                return res(False, "no hubo ningun SELECT que comparar")
            if cab.columnas is not None and consulta.columnas != cab.columnas:
                return res(False, f"columnas {consulta.columnas} != esperadas {cab.columnas}")
            if cab.filas is not None and len(consulta.filas) != cab.filas:
                return res(False, f"{len(consulta.filas)} fila(s) != esperadas {cab.filas}")
            if cab.resultado is not None:
                obtenido = [[formatear(v) for v in fila] for fila in consulta.filas]
                if obtenido != cab.resultado:
                    return res(False, f"resultado {obtenido} != esperado {cab.resultado}")
        planes = [nota for r in resultado.resultados for nota in r.plan]
        for texto in cab.plan:
            if not any(texto in nota for nota in planes):
                return res(False, f"ningun plan contiene {texto!r}: {planes}")
        for texto in cab.no_plan:
            if any(texto in nota for nota in planes):
                return res(False, f"algun plan contiene {texto!r} y no deberia: {planes}")
        for archivo in cab.existe:
            if not (db.ruta / archivo).exists():
                return res(False, f"no existe {archivo}")
        for archivo in cab.no_existe:
            if (db.ruta / archivo).exists():
                return res(False, f"existe {archivo} y no deberia")
        for archivo, texto in cab.contiene:
            ruta_archivo = db.ruta / archivo
            if not ruta_archivo.exists() or texto not in ruta_archivo.read_text(encoding="utf-8"):
                return res(False, f"{archivo} no contiene {texto!r}")
        return res(True)


def listar_archivos() -> list[Path]:
    """Todos los .sql de la bateria (validos + invalidos), sin pruebas/demo/ ni pruebas/bases/."""
    return sorted(RAIZ.glob("*/validos/*.sql")) + sorted(RAIZ.glob("*/invalidos/*.sql"))


def ejecutar_bateria() -> list[ResultadoPrueba]:
    return [_evaluar(ruta) for ruta in listar_archivos()]


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    resultados = ejecutar_bateria()
    fallos = [r for r in resultados if not r.paso]
    print(f"{len(resultados) - len(fallos)}/{len(resultados)} pasaron")
    for r in fallos:
        print(f"{r}: {r.razon}")
