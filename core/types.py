"""
Tipos de datos SQL y su representacion en Python y en disco.

    INT         -> int
    FLOAT       -> float
    VARCHAR(n)  -> str (longitud maxima n)
    BOOLEAN     -> bool
    DATE        -> datetime.date (texto YYYY-MM-DD)
    NULL        -> None (tipo de la constante NULL; compatible con todo)

Ojo: en Python `bool` es subclase de `int`, por eso aqui se usa
`type(v) is int` y no `isinstance(v, int)`.
"""

from __future__ import annotations

import datetime
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TipoSQL:
    nombre: str              # INT, FLOAT, VARCHAR, BOOLEAN, DATE, NULL
    longitud: int | None = None  # solo VARCHAR; None = sin limite (resultado de ||)

    def __str__(self) -> str:
        if self.nombre == "VARCHAR" and self.longitud is not None:
            return f"VARCHAR({self.longitud})"
        return self.nombre

    @property
    def es_numerico(self) -> bool:
        return self.nombre in ("INT", "FLOAT")

    @property
    def es_nulo(self) -> bool:
        return self.nombre == "NULL"


INT = TipoSQL("INT")
FLOAT = TipoSQL("FLOAT")
VARCHAR = TipoSQL("VARCHAR")
BOOLEAN = TipoSQL("BOOLEAN")
DATE = TipoSQL("DATE")
NULO = TipoSQL("NULL")

_RE_TIPO = re.compile(r"^(INT|FLOAT|BOOLEAN|DATE|VARCHAR\((\d+)\))$", re.I)
_RE_FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def parsear_tipo(texto: str) -> TipoSQL:
    """'VARCHAR(20)' -> TipoSQL('VARCHAR', 20). Lo usa el catalogo al leer metadata.txt."""
    m = _RE_TIPO.match(texto.strip())
    if not m:
        raise ValueError(f"tipo desconocido: {texto!r}")
    if m.group(2) is not None:
        return TipoSQL("VARCHAR", int(m.group(2)))
    return TipoSQL(m.group(1).upper())


def parsear_fecha(texto: str) -> datetime.date | None:
    """'2024-02-29' -> date; None si el formato o la fecha no son validos."""
    if not _RE_FECHA.match(texto):
        return None
    try:
        return datetime.date.fromisoformat(texto)
    except ValueError:
        return None


def tipo_de_valor(valor) -> TipoSQL:
    if valor is None:
        return NULO
    if type(valor) is bool:
        return BOOLEAN
    if type(valor) is int:
        return INT
    if type(valor) is float:
        return FLOAT
    if isinstance(valor, datetime.date):
        return DATE
    return VARCHAR


# ---------------------------------------------------------------------------
# Compatibilidad (analisis semantico)
# ---------------------------------------------------------------------------

def comparables(a: TipoSQL, b: TipoSQL) -> bool:
    """Se pueden comparar con =, <, IN, BETWEEN..."""
    if a.es_nulo or b.es_nulo:
        return True
    if a.es_numerico and b.es_numerico:
        return True
    return a.nombre == b.nombre


def asignable(destino: TipoSQL, origen: TipoSQL) -> bool:
    """Un valor de tipo `origen` se puede guardar en una columna `destino`."""
    if origen.es_nulo:
        return True
    if destino.nombre == "FLOAT":
        return origen.es_numerico
    return destino.nombre == origen.nombre


def tipo_comun(a: TipoSQL, b: TipoSQL) -> TipoSQL:
    """Tipo resultante de combinar dos ramas (p. ej. resultado de + o de IN)."""
    if a.es_nulo:
        return b
    if b.es_nulo:
        return a
    if a.es_numerico and b.es_numerico:
        return FLOAT if FLOAT.nombre in (a.nombre, b.nombre) else INT
    if a.nombre == "VARCHAR" and b.nombre == "VARCHAR":
        if a.longitud is None or b.longitud is None:
            return VARCHAR
        return TipoSQL("VARCHAR", max(a.longitud, b.longitud))
    return a


# ---------------------------------------------------------------------------
# Conversion en tiempo de ejecucion
# ---------------------------------------------------------------------------

class ValorInvalido(Exception):
    pass


def convertir_para_columna(valor, tipo: TipoSQL):
    """
    Valida/convierte `valor` para guardarlo en una columna de tipo `tipo`.
    Lanza ValorInvalido con un mensaje para el usuario si no se puede.
    """
    if valor is None:
        return None
    n = tipo.nombre
    if n == "INT":
        if type(valor) is int:
            return valor
    elif n == "FLOAT":
        if type(valor) in (int, float):
            return float(valor)
    elif n == "VARCHAR":
        if type(valor) is str:
            if tipo.longitud is not None and len(valor) > tipo.longitud:
                raise ValorInvalido(
                    f"el texto '{_recortar(valor)}' tiene {len(valor)} caracteres y excede {tipo}")
            return valor
    elif n == "BOOLEAN":
        if type(valor) is bool:
            return valor
    elif n == "DATE":
        if isinstance(valor, datetime.date):
            return valor
        if type(valor) is str:
            fecha = parsear_fecha(valor)
            if fecha is None:
                raise ValorInvalido(f"'{valor}' no es una fecha válida (formato YYYY-MM-DD)")
            return fecha
    raise ValorInvalido(f"el valor {formatear(valor)} ({tipo_de_valor(valor)}) no es compatible con {tipo}")


def _recortar(texto: str, n: int = 30) -> str:
    return texto if len(texto) <= n else texto[:n - 3] + "..."


# ---------------------------------------------------------------------------
# Serializacion a disco (CSV e indices)
# ---------------------------------------------------------------------------
#
# NULL se escribe como \N. En los textos se escapan '\', salto de linea y
# retorno de carro, para que cada registro ocupe exactamente una linea.

NULL_EN_DISCO = r"\N"


def serializar(valor) -> str:
    if valor is None:
        return NULL_EN_DISCO
    if type(valor) is bool:
        return "TRUE" if valor else "FALSE"
    if type(valor) is float:
        return repr(valor)
    if isinstance(valor, datetime.date):
        return valor.isoformat()
    if type(valor) is str:
        return valor.replace("\\", "\\\\").replace("\n", "\\n").replace("\r", "\\r")
    return str(valor)


def _desescapar(texto: str) -> str:
    if "\\" not in texto:
        return texto
    salida = []
    i = 0
    while i < len(texto):
        c = texto[i]
        if c == "\\" and i + 1 < len(texto):
            sig = texto[i + 1]
            salida.append({"n": "\n", "r": "\r", "\\": "\\"}.get(sig, sig))
            i += 2
            continue
        salida.append(c)
        i += 1
    return "".join(salida)


def deserializar(texto: str, tipo: TipoSQL):
    if texto == NULL_EN_DISCO:
        return None
    n = tipo.nombre
    if n == "INT":
        return int(texto)
    if n == "FLOAT":
        return float(texto)
    if n == "BOOLEAN":
        return texto.upper() == "TRUE"
    if n == "DATE":
        return datetime.date.fromisoformat(texto)
    return _desescapar(texto)


# ---------------------------------------------------------------------------
# Presentacion
# ---------------------------------------------------------------------------

def formatear(valor) -> str:
    """Valor -> texto para mostrar en resultados (NULL, TRUE, 3.5, 2024-01-01)."""
    if valor is None:
        return "NULL"
    if type(valor) is bool:
        return "TRUE" if valor else "FALSE"
    if type(valor) is float:
        if valor.is_integer() and abs(valor) < 1e15:
            return f"{valor:.1f}"
        return f"{round(valor, 6):g}" if abs(valor) >= 1e-4 else repr(valor)
    if isinstance(valor, datetime.date):
        return valor.isoformat()
    return str(valor)


def literal_sql(valor) -> str:
    """Valor -> literal SQL (lo usa metadata.txt para los DEFAULT)."""
    if valor is None:
        return "NULL"
    if type(valor) is bool:
        return "TRUE" if valor else "FALSE"
    if isinstance(valor, datetime.date):
        return f"DATE '{valor.isoformat()}'"
    if type(valor) is str:
        return "'" + valor.replace("'", "''") + "'"
    return repr(valor) if type(valor) is float else str(valor)


_RE_LITERAL = re.compile(r"^(?:NULL|TRUE|FALSE|DATE '(\d{4}-\d{2}-\d{2})'|'((?:[^']|'')*)'|(-?(?:\d+\.\d*(?:e[-+]?\d+)?|\d+e[-+]?\d+))|(-?\d+))$",
                         re.I)


def parsear_literal_sql(texto: str):
    """Inverso de literal_sql."""
    texto = texto.strip()
    m = _RE_LITERAL.match(texto)
    if not m:
        raise ValueError(f"literal invalido: {texto!r}")
    fecha, cadena, flotante, entero = m.groups()
    if fecha is not None:
        return datetime.date.fromisoformat(fecha)
    if cadena is not None:
        return cadena.replace("''", "'")
    if flotante is not None:
        return float(flotante)
    if entero is not None:
        return int(entero)
    return {"NULL": None, "TRUE": True, "FALSE": False}[texto.upper()]
