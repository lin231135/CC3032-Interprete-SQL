"""
Dibujo del arbol sintactico (ParseTree de ANTLR) y del AST, en memoria
(graphviz `.pipe()`, sin archivos temporales). Lo usan las pestanas "Arbol
sintactico" y "AST" del IDE; `ast_texto` tambien lo usa la CLI.

`max_nodos` corta el recorrido para no colgar el IDE con scripts grandes.
"""

from __future__ import annotations

import datetime
import shutil

import graphviz
from antlr4.tree.Tree import TerminalNode

from core.types import TipoSQL, formatear

from arbol import nodes as n


def dot_disponible() -> bool:
    """True si el binario `dot` de Graphviz esta en el PATH."""
    return shutil.which("dot") is not None


# ---------------------------------------------------------------------------
# Arbol sintactico
# ---------------------------------------------------------------------------

def parse_tree_png(tree, rule_names: list[str], max_nodos: int = 500) -> bytes:
    grafo = graphviz.Digraph(format="png")
    grafo.attr("node", fontname="Segoe UI", fontsize="11")
    grafo.attr(dpi="90")
    contador = [0]

    def agregar(nodo, id_padre: str | None) -> None:
        if contador[0] >= max_nodos:
            return
        id_actual = str(contador[0])
        contador[0] += 1
        if isinstance(nodo, TerminalNode):
            grafo.node(id_actual, nodo.getText(), shape="box", style="filled", fillcolor="lightyellow")
        else:
            grafo.node(id_actual, rule_names[nodo.getRuleIndex()], shape="ellipse", style="filled",
                       fillcolor="lightblue")
        if id_padre is not None:
            grafo.edge(id_padre, id_actual)
        if not isinstance(nodo, TerminalNode):
            for i in range(nodo.getChildCount()):
                if contador[0] >= max_nodos:
                    break
                agregar(nodo.getChild(i), id_actual)

    agregar(tree, None)
    return grafo.pipe(format="png")


def parse_tree_texto(tree, parser) -> str:
    """Arbol sintactico indentado (fallback sin Graphviz)."""
    lineas: list[str] = []

    def agregar(nodo, nivel: int) -> None:
        if isinstance(nodo, TerminalNode):
            lineas.append("  " * nivel + repr(nodo.getText()))
            return
        lineas.append("  " * nivel + parser.ruleNames[nodo.getRuleIndex()])
        for i in range(nodo.getChildCount()):
            agregar(nodo.getChild(i), nivel + 1)

    agregar(tree, 0)
    return "\n".join(lineas)


# ---------------------------------------------------------------------------
# AST
# ---------------------------------------------------------------------------

def _valor(v) -> str:
    if isinstance(v, TipoSQL):
        return str(v)
    if isinstance(v, (bool, int, float, datetime.date)) or v is None:
        return formatear(v)
    if isinstance(v, str):
        return v
    if isinstance(v, tuple):
        return ".".join(map(str, v))
    if isinstance(v, list):
        return ", ".join(_valor(x) for x in v)
    return str(v)


def etiqueta_ast(nodo: n.Nodo) -> str:
    """'BinaryOp' + atributos simples: op: >="""
    partes = [type(nodo).__name__]
    if isinstance(nodo, n.Literal):
        partes.append(f"'{nodo.valor}'" if isinstance(nodo.valor, str) else _valor(nodo.valor))
    for nombre, valor in n.atributos(nodo):
        if nombre in ("tipo_literal", "valor") and isinstance(nodo, n.Literal):
            continue
        partes.append(f"{nombre}: {_valor(valor)}")
    tipo = getattr(nodo, "tipo", None)
    if isinstance(nodo, n.Expr) and tipo is not None:
        partes.append(f"⟨{tipo}⟩")
    return "\n".join(partes)


def ast_png(script: n.Script, max_nodos: int = 500) -> bytes:
    grafo = graphviz.Digraph(format="png")
    grafo.attr("node", fontname="Segoe UI", fontsize="11", shape="box", style="rounded,filled")
    grafo.attr("edge", fontname="Segoe UI", fontsize="9", fontcolor="#555555")
    grafo.attr(dpi="90")
    contador = [0]

    def color(nodo) -> str:
        if isinstance(nodo, n.Sentencia):
            return "#c9e4ff"
        if isinstance(nodo, (n.Literal,)):
            return "#fff2c2"
        if isinstance(nodo, n.ColumnRef):
            return "#d5f5e3"
        if isinstance(nodo, n.Aggregate):
            return "#fde2c8"
        if isinstance(nodo, n.Expr):
            return "#eeeeee"
        return "#f6f6f6"

    def agregar(nodo: n.Nodo, id_padre: str | None, etiqueta_arista: str) -> None:
        if contador[0] >= max_nodos:
            return
        id_actual = str(contador[0])
        contador[0] += 1
        grafo.node(id_actual, etiqueta_ast(nodo), fillcolor=color(nodo))
        if id_padre is not None:
            grafo.edge(id_padre, id_actual, label=etiqueta_arista)
        for campo, hijo in n.campos_hijos(nodo):
            agregar(hijo, id_actual, campo)

    agregar(script, None, "")
    return grafo.pipe(format="png")


def ast_texto(script: n.Script) -> str:
    lineas: list[str] = []

    def agregar(nodo: n.Nodo, prefijo: str, campo: str, nivel: int) -> None:
        etiqueta = etiqueta_ast(nodo).replace("\n", "  ")
        lineas.append(f"{'  ' * nivel}{campo + ': ' if campo else ''}{etiqueta}")
        for c, hijo in n.campos_hijos(nodo):
            agregar(hijo, prefijo, c, nivel + 1)

    agregar(script, "", "", 0)
    return "\n".join(lineas)
