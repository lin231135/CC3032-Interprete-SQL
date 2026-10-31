"""
Punto de entrada unico del interprete: analizar(sql, db) -> Resultado.

Pipeline (enunciado, "Funcionamiento Esperado"):
  1. ANTLR: lexer (tokens) + parser (arbol sintactico); errores lexicos y
     sintacticos con su linea:columna.
  2. ASTBuilder: arbol sintactico -> AST (arbol/nodes.py).
  3. SemanticAnalyzer: valida TODO el script contra una copia del catalogo y
     anota el AST.
  4. Si no hubo errores y se pidio ejecutar: el Ejecutor corre sentencia por
     sentencia sobre los archivos de la base de datos.

Lo usan el IDE, la CLI (main.py), la bateria de pruebas y pytest. Nadie mas
debe instanciar el lexer/parser de ANTLR por su cuenta.
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field

from antlr4 import CommonTokenStream, InputStream, Token
from antlr4.error.ErrorListener import ErrorListener

from almacenamiento.database import Database
from arbol.builder import construir_ast
from arbol.nodes import Script
from core.errors import SQLError, traducir_mensaje_antlr
from generated.SQLLexer import SQLLexer
from generated.SQLParser import SQLParser
from interprete.executor import Ejecutor
from interprete.results import ResultadoSentencia
from semantico.analyzer import SemanticAnalyzer

RAIZ = pathlib.Path(__file__).resolve().parent
BD_POR_DEFECTO = RAIZ / "database"


class _ListenerDeErrores(ErrorListener):
    """Acumula los errores de ANTLR (en vez de imprimirlos en stderr), traducidos al espanol."""

    def __init__(self, errores: list[SQLError], fase: str):
        super().__init__()
        self._errores = errores
        self._fase = fase

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self._errores.append(SQLError(line, column + 1, self._fase, self._fase, traducir_mensaje_antlr(msg)))


@dataclass
class TokenInfo:
    tipo: str
    lexema: str
    linea: int
    columna: int


@dataclass
class Resultado:
    fuente: str
    tokens: list[TokenInfo] = field(default_factory=list)
    tree: object | None = None
    parser: object | None = None
    ast: Script | None = None
    errores_lexicos: list[SQLError] = field(default_factory=list)
    errores_sintacticos: list[SQLError] = field(default_factory=list)
    errores_semanticos: list[SQLError] = field(default_factory=list)
    errores_ejecucion: list[SQLError] = field(default_factory=list)
    resultados: list[ResultadoSentencia] = field(default_factory=list)
    ejecutado: bool = False

    @property
    def errores(self) -> list[SQLError]:
        """Errores de analisis + ejecucion, ordenados por (linea, columna)."""
        return sorted(
            [*self.errores_lexicos, *self.errores_sintacticos, *self.errores_semanticos, *self.errores_ejecucion],
            key=lambda e: (e.line, e.column),
        )

    @property
    def errores_analisis(self) -> list[SQLError]:
        return [e for e in self.errores if e.fase != "ejecucion"]

    @property
    def ok(self) -> bool:
        return not self.errores

    @property
    def ultima_consulta(self) -> ResultadoSentencia | None:
        return next((r for r in reversed(self.resultados) if r.es_consulta and r.ok), None)


def analizar(fuente: str, db: Database | None = None, ejecutar: bool = False) -> Resultado:
    """
    Analiza (y opcionalmente ejecuta) `fuente`. Sin `db` el analisis
    semantico usa un catalogo vacio y no se puede ejecutar.
    """
    resultado = Resultado(fuente=fuente)

    lexer = SQLLexer(InputStream(fuente))
    lexer.removeErrorListeners()
    lexer.addErrorListener(_ListenerDeErrores(resultado.errores_lexicos, "lexico"))
    tokens = CommonTokenStream(lexer)
    tokens.fill()
    nombres = lexer.symbolicNames
    resultado.tokens = [
        TokenInfo(nombres[t.type] if 0 < t.type < len(nombres) else str(t.type), t.text, t.line, t.column + 1)
        for t in tokens.tokens if t.type != Token.EOF
    ]

    parser = SQLParser(tokens)
    parser.removeErrorListeners()
    parser.addErrorListener(_ListenerDeErrores(resultado.errores_sintacticos, "sintactico"))
    resultado.tree = parser.script()
    resultado.parser = parser

    if resultado.errores_lexicos or resultado.errores_sintacticos:
        return resultado

    resultado.ast, errores_ast = construir_ast(resultado.tree)
    catalogo = db.catalogo if db is not None else None
    if catalogo is None:
        from almacenamiento.catalog import Catalog

        catalogo = Catalog()
    analizador = SemanticAnalyzer(catalogo)
    resultado.errores_semanticos = errores_ast + analizador.analizar(resultado.ast)

    if ejecutar and db is not None and not resultado.errores_semanticos:
        resultado.resultados, resultado.errores_ejecucion = Ejecutor(db).ejecutar_script(resultado.ast)
        resultado.ejecutado = True
    return resultado


def ejecutar(fuente: str, db: Database) -> Resultado:
    return analizar(fuente, db, ejecutar=True)


def analizar_archivo(ruta: str | pathlib.Path, db: Database | None = None, ejecutar: bool = False) -> Resultado:
    fuente = pathlib.Path(ruta).read_text(encoding="utf-8")
    return analizar(fuente, db, ejecutar)
