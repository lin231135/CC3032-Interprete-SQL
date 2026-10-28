"""
Nodos del AST (arbol de sintaxis abstracta).

El ASTBuilder (arbol/builder.py) los construye a partir del arbol sintactico
de ANTLR; el analisis semantico los ANOTA (campos `ref_*`, `tipo`,
`columnas_salida`...) y el interprete los ejecuta. Las anotaciones y la
posicion (`linea`, `columna`) se declaran con compare=False para que la
igualdad sea ESTRUCTURAL: el analizador la usa para saber si una expresion
del SELECT es la misma que una del GROUP BY.
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields

from core.types import TipoSQL


def _pos():
    return field(default=0, kw_only=True, compare=False, repr=False)


def _anotacion(default=None):
    return field(default=default, kw_only=True, compare=False, repr=False)


@dataclass
class Nodo:
    linea: int = _pos()
    columna: int = _pos()


# ---------------------------------------------------------------------------
# Expresiones
# ---------------------------------------------------------------------------

@dataclass
class Expr(Nodo):
    texto: str = field(default="", kw_only=True, compare=False, repr=False)  # SQL original
    tipo: TipoSQL | None = _anotacion()


@dataclass
class Literal(Expr):
    valor: object
    tipo_literal: TipoSQL


@dataclass
class ColumnRef(Expr):
    tabla: str | None
    nombre: str
    # anotaciones del analisis semantico
    ref_alias: str | None = _anotacion()   # alias de la tabla a la que pertenece
    ref_nivel: int = _anotacion(0)         # 0 = consulta actual, 1 = consulta externa...


@dataclass
class UnaryOp(Expr):
    op: str            # '-', '+', 'NOT'
    operando: Expr


@dataclass
class BinaryOp(Expr):
    op: str            # + - * / % || = <> < <= > >= AND OR
    izquierda: Expr
    derecha: Expr


@dataclass
class IsNull(Expr):
    expr: Expr
    negado: bool


@dataclass
class Between(Expr):
    expr: Expr
    desde: Expr
    hasta: Expr
    negado: bool


@dataclass
class Like(Expr):
    expr: Expr
    patron: Expr
    negado: bool


@dataclass
class InList(Expr):
    expr: Expr
    valores: list[Expr]
    negado: bool


@dataclass
class InSubquery(Expr):
    expr: Expr
    consulta: "Select"
    negado: bool


@dataclass
class Exists(Expr):
    consulta: "Select"
    negado: bool


@dataclass
class ScalarSubquery(Expr):
    consulta: "Select"


@dataclass
class Aggregate(Expr):
    funcion: str        # COUNT, SUM, AVG, MIN, MAX
    argumento: Expr | None  # None = COUNT(*)
    distinct: bool


# ---------------------------------------------------------------------------
# SELECT
# ---------------------------------------------------------------------------

@dataclass
class SelectItem(Nodo):
    pass


@dataclass
class Star(SelectItem):
    tabla: str | None   # None = *, 'e' = e.*


@dataclass
class SelectExpr(SelectItem):
    expr: Expr
    alias: str | None


@dataclass
class FromItem(Nodo):
    tabla: str
    alias: str
    union: str          # BASE, INNER, LEFT, CROSS
    condicion: Expr | None


@dataclass
class OrderItem(Nodo):
    expr: Expr
    descendente: bool
    # si ORDER BY se refiere a una columna del resultado (alias o posicion)
    indice_salida: int | None = _anotacion()


@dataclass
class ColumnaSalida:
    nombre: str
    tipo: TipoSQL
    expr: Expr          # expresion que la calcula (las * se expanden a ColumnRef)


@dataclass
class Sentencia(Nodo):
    texto: str = field(default="", kw_only=True, compare=False, repr=False)


@dataclass
class Select(Sentencia):
    distinct: bool
    items: list[SelectItem]
    desde: list[FromItem]
    where: Expr | None
    group_by: list[Expr]
    having: Expr | None
    order_by: list[OrderItem]
    limit: int | None
    offset: int | None
    # anotaciones
    columnas_salida: list[ColumnaSalida] = _anotacion()
    agrupado: bool = _anotacion(False)
    correlacionada: bool = _anotacion(False)


# ---------------------------------------------------------------------------
# DDL
# ---------------------------------------------------------------------------

@dataclass
class ColumnDef(Nodo):
    nombre: str
    tipo_dato: TipoSQL
    not_null: bool = False
    primary_key: bool = False
    unique: bool = False
    default: Literal | None = None
    referencia: tuple[str, str] | None = None   # (tabla, columna)


@dataclass
class ForeignKey(Nodo):
    columna_local: str
    tabla_ref: str
    columna_ref: str


@dataclass
class CreateTable(Sentencia):
    nombre: str
    columnas: list[ColumnDef]
    primary_key: list[str]          # restriccion de tabla PRIMARY KEY (a, b)
    uniques: list[list[str]]
    foraneas: list[ForeignKey]
    si_no_existe: bool


@dataclass
class DropTable(Sentencia):
    nombre: str
    si_existe: bool


@dataclass
class CreateIndex(Sentencia):
    nombre: str
    tabla: str
    columna_indice: str
    unico: bool
    pos_tabla: Nodo | None = _anotacion()     # ubicacion de los identificadores (para los errores)
    pos_columna: Nodo | None = _anotacion()


@dataclass
class DropIndex(Sentencia):
    nombre: str
    si_existe: bool


# ---------------------------------------------------------------------------
# DML
# ---------------------------------------------------------------------------

@dataclass
class Insert(Sentencia):
    tabla: str
    columnas: list[str] | None
    filas: list[list[Expr]] | None
    consulta: Select | None
    pos_tabla: Nodo | None = _anotacion()
    pos_columnas: list[Nodo] = _anotacion()


@dataclass
class Assignment(Nodo):
    columna_destino: str
    valor: Expr


@dataclass
class Update(Sentencia):
    tabla: str
    asignaciones: list[Assignment]
    where: Expr | None
    pos_tabla: Nodo | None = _anotacion()


@dataclass
class Delete(Sentencia):
    tabla: str
    where: Expr | None
    pos_tabla: Nodo | None = _anotacion()


@dataclass
class Script(Nodo):
    sentencias: list[Sentencia]


# ---------------------------------------------------------------------------
# Recorrido generico
# ---------------------------------------------------------------------------

def campos_hijos(nodo: Nodo):
    """(nombre_campo, hijo) de cada hijo Nodo; las listas se aplanan con su indice."""
    for f in fields(nodo):
        if not f.compare or f.name in ("linea", "columna"):
            continue
        valor = getattr(nodo, f.name)
        if isinstance(valor, Nodo):
            yield f.name, valor
        elif isinstance(valor, list):
            for i, elem in enumerate(valor):
                if isinstance(elem, Nodo):
                    yield f"{f.name}[{i}]", elem
                elif isinstance(elem, list):
                    for j, sub in enumerate(elem):
                        if isinstance(sub, Nodo):
                            yield f"{f.name}[{i}][{j}]", sub


def hijos(nodo: Nodo) -> list[Nodo]:
    return [h for _, h in campos_hijos(nodo)]


def atributos(nodo: Nodo) -> list[tuple[str, object]]:
    """Campos que NO son nodos (para etiquetar el AST al dibujarlo)."""
    salida = []
    for f in fields(nodo):
        if not f.compare or f.name in ("linea", "columna"):
            continue
        valor = getattr(nodo, f.name)
        if isinstance(valor, Nodo):
            continue
        if isinstance(valor, list) and valor and all(isinstance(v, (Nodo, list)) for v in valor):
            continue
        if isinstance(valor, list) and not valor:
            continue
        if valor is None or valor is False:
            continue
        salida.append((f.name, valor))
    return salida


def recorrer(nodo: Nodo, entrar_subconsultas: bool = True):
    """Preorden. Con entrar_subconsultas=False no baja a SELECTs anidados."""
    yield nodo
    for h in hijos(nodo):
        if not entrar_subconsultas and isinstance(h, Select):
            continue
        yield from recorrer(h, entrar_subconsultas)
