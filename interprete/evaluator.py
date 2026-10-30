"""
Evaluacion de expresiones sobre un registro (o un grupo de registros).

Un Entorno es la "fila actual" de una consulta: `fila` mapea alias de tabla
-> {columna: valor}. `padre` es el entorno de la consulta externa (para las
subconsultas correlacionadas: una ColumnRef con ref_nivel=k sube k padres) y
`grupo`, en una consulta agrupada, es la lista de filas del grupo sobre la
que se calculan COUNT/SUM/AVG/MIN/MAX.

Logica de tres valores de SQL: cualquier comparacion con NULL da NULL
(desconocido, None en Python); WHERE/HAVING/ON solo conservan las filas cuya
condicion es TRUE.
"""

from __future__ import annotations

import math
import operator
import re

from core.errors import ErrorEjecucion
from core.types import formatear

from arbol import nodes as n


class Entorno:
    __slots__ = ("fila", "padre", "grupo")

    def __init__(self, fila: dict, padre: "Entorno | None" = None, grupo: list[dict] | None = None):
        self.fila = fila
        self.padre = padre
        self.grupo = grupo


_COMPARACIONES = {
    "=": operator.eq,
    "<>": operator.ne,
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
}

_INVERTIR = {"=": "=", "<>": "<>", "<": ">", "<=": ">=", ">": "<", ">=": "<="}


def es_verdadero(valor) -> bool:
    return valor is True


class Evaluador:
    def __init__(self, ejecutor):
        self.ejecutor = ejecutor  # para correr subconsultas
        self._patrones: dict[str, re.Pattern] = {}
        self._despacho = {
            n.Literal: lambda e, env: e.valor,
            n.ColumnRef: self._columna,
            n.UnaryOp: self._unaria,
            n.BinaryOp: self._binaria,
            n.IsNull: self._is_null,
            n.Between: self._between,
            n.Like: self._like,
            n.InList: self._in_lista,
            n.InSubquery: self._in_subconsulta,
            n.Exists: self._exists,
            n.ScalarSubquery: self._escalar,
            n.Aggregate: self._agregado,
        }

    def eval(self, e: n.Expr, env: Entorno):
        return self._despacho[type(e)](e, env)

    # ------------------------------------------------------------------

    def _columna(self, e: n.ColumnRef, env: Entorno):
        for _ in range(e.ref_nivel):
            env = env.padre
        return env.fila[e.ref_alias][e.nombre]

    def _unaria(self, e: n.UnaryOp, env: Entorno):
        v = self.eval(e.operando, env)
        if v is None:
            return None
        if e.op == "NOT":
            return not v
        return -v

    def _binaria(self, e: n.BinaryOp, env: Entorno):
        op = e.op
        if op == "AND":
            izq = self.eval(e.izquierda, env)
            if izq is False:
                return False
            der = self.eval(e.derecha, env)
            if der is False:
                return False
            return None if izq is None or der is None else True
        if op == "OR":
            izq = self.eval(e.izquierda, env)
            if izq is True:
                return True
            der = self.eval(e.derecha, env)
            if der is True:
                return True
            return None if izq is None or der is None else False

        izq = self.eval(e.izquierda, env)
        der = self.eval(e.derecha, env)
        if izq is None or der is None:
            return None
        comparar = _COMPARACIONES.get(op)
        if comparar is not None:
            return comparar(izq, der)
        if op == "||":
            return (izq if type(izq) is str else formatear(izq)) + (der if type(der) is str else formatear(der))
        if op == "+":
            return izq + der
        if op == "-":
            return izq - der
        if op == "*":
            return izq * der
        if der == 0:
            raise ErrorEjecucion(e, "ejecucion", f"División entre cero en '{e.texto}'")
        if op == "/":
            return izq / der
        resto = math.fmod(izq, der)  # signo del dividendo, como en SQL
        return int(resto) if type(izq) is int and type(der) is int else resto

    def _is_null(self, e: n.IsNull, env: Entorno):
        return (self.eval(e.expr, env) is None) != e.negado

    def _between(self, e: n.Between, env: Entorno):
        v, desde, hasta = self.eval(e.expr, env), self.eval(e.desde, env), self.eval(e.hasta, env)
        if v is None or desde is None or hasta is None:
            return None
        return (desde <= v <= hasta) != e.negado

    def _like(self, e: n.Like, env: Entorno):
        v, patron = self.eval(e.expr, env), self.eval(e.patron, env)
        if v is None or patron is None:
            return None
        regex = self._patrones.get(patron)
        if regex is None:
            partes = ["." if c == "_" else ".*" if c == "%" else re.escape(c) for c in patron]
            regex = self._patrones[patron] = re.compile("".join(partes), re.S)
        return (regex.fullmatch(v) is not None) != e.negado

    @staticmethod
    def _pertenece(v, valores: list, negado: bool):
        if v is None:
            return None
        if v in [x for x in valores if x is not None]:
            return not negado
        if any(x is None for x in valores):
            return None
        return negado

    def _in_lista(self, e: n.InList, env: Entorno):
        v = self.eval(e.expr, env)
        if v is None:
            return None
        return self._pertenece(v, [self.eval(x, env) for x in e.valores], e.negado)

    def _in_subconsulta(self, e: n.InSubquery, env: Entorno):
        v = self.eval(e.expr, env)
        if v is None:
            return None
        valores = [fila[0] for fila in self.ejecutor.subconsulta(e.consulta, env)]
        return self._pertenece(v, valores, e.negado)

    def _exists(self, e: n.Exists, env: Entorno):
        return bool(self.ejecutor.subconsulta(e.consulta, env)) != e.negado

    def _escalar(self, e: n.ScalarSubquery, env: Entorno):
        filas = self.ejecutor.subconsulta(e.consulta, env)
        if len(filas) > 1:
            raise ErrorEjecucion(e, "subconsulta", f"La subconsulta escalar retornó {len(filas)} registros "
                                                   "(debe retornar a lo sumo uno)", fase="ejecucion")
        return filas[0][0] if filas else None

    def _agregado(self, e: n.Aggregate, env: Entorno):
        grupo = env.grupo
        if grupo is None:
            raise ErrorEjecucion(e, "ejecucion", f"Agregación fuera de una consulta agrupada: {e.texto}")
        if e.argumento is None:
            return len(grupo)
        valores = [self.eval(e.argumento, Entorno(fila, env.padre)) for fila in grupo]
        valores = [v for v in valores if v is not None]
        if e.distinct:
            valores = list(dict.fromkeys(valores))
        if e.funcion == "COUNT":
            return len(valores)
        if not valores:
            return None
        if e.funcion == "SUM":
            return sum(valores)
        if e.funcion == "AVG":
            return sum(valores) / len(valores)
        if e.funcion == "MIN":
            return min(valores)
        return max(valores)


def invertir_comparacion(op: str) -> str:
    """a < b  <=>  b > a"""
    return _INVERTIR[op]
