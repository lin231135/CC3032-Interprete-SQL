"""
Errores del interprete, compartidos por todas las fases.

Cada error lleva su FASE (lexico, sintactico, semantico, ejecucion), una
CATEGORIA mas fina (la que usa la bateria de pruebas con `-- @error:`) y su
ubicacion (linea:columna). Nadie lanza excepciones ni hace print() para
reportar errores del usuario: se acumulan en un ErrorReporter para que el IDE
pueda mostrarlos todos de una sola pasada.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

FASES = ("lexico", "sintactico", "semantico", "ejecucion")

# categoria -> fase por defecto
CATEGORIAS = {
    "lexico": "lexico",
    "sintactico": "sintactico",
    "tabla": "semantico",         # tabla inexistente o duplicada
    "columna": "semantico",       # columna inexistente o duplicada
    "tipo": "semantico",          # tipos incompatibles
    "valor": "semantico",         # valores incorrectos en INSERT / UPDATE
    "referencia": "semantico",    # referencias ambiguas o invalidas
    "indice": "semantico",        # indice inexistente o duplicado
    "subconsulta": "semantico",   # subconsulta con mas de una columna / registro
    "agregacion": "semantico",    # uso invalido de agregaciones o GROUP BY
    "restriccion": "ejecucion",   # PRIMARY KEY, UNIQUE, NOT NULL, FOREIGN KEY
    "ejecucion": "ejecucion",     # division entre cero y otros errores en tiempo de ejecucion
}

NOMBRE_FASE = {
    "lexico": "Léxico",
    "sintactico": "Sintáctico",
    "semantico": "Semántico",
    "ejecucion": "Ejecución",
}


@dataclass
class SQLError:
    line: int
    column: int
    fase: str
    category: str
    message: str

    def __str__(self) -> str:
        return f"[{self.category}] linea {self.line}:{self.column} - {self.message}"


class ErrorEjecucion(Exception):
    """Error en tiempo de ejecucion; el executor lo convierte en SQLError."""

    def __init__(self, nodo, category: str, message: str, fase: str | None = None):
        super().__init__(message)
        self.nodo = nodo
        self.category = category
        self.message = message
        self.fase = fase or CATEGORIAS[category]

    def a_error(self) -> SQLError:
        linea = getattr(self.nodo, "linea", 0) or 0
        columna = getattr(self.nodo, "columna", 0) or 0
        return SQLError(linea, columna, self.fase, self.category, self.message)


@dataclass
class ErrorReporter:
    errors: list[SQLError] = field(default_factory=list)

    def error(self, nodo, category: str, message: str, fase: str | None = None) -> None:
        """`nodo` es cualquier objeto con `linea` y `columna` (nodos del AST)."""
        assert category in CATEGORIAS, f"categoria desconocida: {category}"
        linea = getattr(nodo, "linea", 0) or 0
        columna = getattr(nodo, "columna", 0) or 0
        self.errors.append(SQLError(linea, columna, fase or CATEGORIAS[category], category, message))

    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def all(self) -> list[SQLError]:
        return list(self.errors)


# ---------------------------------------------------------------------------
# Mensajes de ANTLR -> espanol
# ---------------------------------------------------------------------------

_NOMBRES_TOKENS = {
    "INT_LIT": "un número",
    "FLOAT_LIT": "un número decimal",
    "STRING_LIT": "un texto",
    "IDENTIFIER": "un identificador",
    "<EOF>": "fin de archivo",
}
_MAX_ESPERADOS = 7

_RE_RECONOCIMIENTO = re.compile(r"^token recognition error at: '(.*)'$", re.S)
_RE_INESPERADA = re.compile(r"^(mismatched|extraneous) input '(.*?)' expecting (.*)$", re.S)
_RE_FALTA = re.compile(r"^missing (.*?) at '(.*)'$", re.S)
_RE_INVIABLE = re.compile(r"^no viable alternative at input '(.*)'$", re.S)


def _esperados(texto: str) -> str:
    """"{'FROM', ',', IDENTIFIER}" -> "'FROM', ',' o un identificador" (recortado si es muy largo)."""
    texto = texto.strip()
    elementos = [e.strip() for e in texto[1:-1].split(", ")] if texto.startswith("{") else [texto]
    elementos = [_NOMBRES_TOKENS.get(e, e) for e in elementos]
    if len(elementos) > _MAX_ESPERADOS:
        if "un identificador" in elementos and "un número" in elementos:
            return "una expresión (columna, valor o subconsulta)"
        return ", ".join(elementos[:_MAX_ESPERADOS]) + ", …"
    if len(elementos) == 1:
        return elementos[0]
    return ", ".join(elementos[:-1]) + " o " + elementos[-1]


def _entrada(texto: str) -> str:
    texto = texto.lstrip(";").strip() or texto  # "no viable alternative" incluye el ';' anterior
    return "fin de archivo" if texto == "<EOF>" else f"'{texto}'"


def traducir_mensaje_antlr(msg: str) -> str:
    if m := _RE_RECONOCIMIENTO.match(msg):
        if m.group(1).startswith("'"):
            return f"Texto sin cerrar: falta la comilla final en {m.group(1)}"
        return f"Símbolo no reconocido: '{m.group(1)}'"
    if m := _RE_INESPERADA.match(msg):
        que = "Entrada inesperada" if m.group(1) == "mismatched" else "Entrada sobrante"
        return f"{que} {_entrada(m.group(2))}; se esperaba {_esperados(m.group(3))}"
    if m := _RE_FALTA.match(msg):
        return f"Falta {_esperados(m.group(1))} antes de {_entrada(m.group(2))}"
    if m := _RE_INVIABLE.match(msg):
        return f"Sentencia inválida cerca de {_entrada(m.group(1))}"
    return msg
