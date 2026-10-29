"""
Catalogo de la base de datos: esquemas de tablas, restricciones e indices.

Se guarda en `metadata.txt` con un formato de texto propio, legible y
orientado a lineas (ver docs/Almacenamiento.md):

    TABLA estudiantes
      COLUMNA id INT NOT NULL
      COLUMNA nombre VARCHAR(50) NOT NULL
      COLUMNA edad INT NULL DEFAULT 18
      PRIMARY KEY (id)
      UNIQUE (carnet)
      FOREIGN KEY (curso_id) REFERENCES cursos (id)
    FIN
    INDICE idx_edad ON estudiantes (edad)
    INDICE UNICO idx_carnet ON estudiantes (carnet)

El analizador semantico trabaja sobre una COPIA del catalogo (`copia()`) a la
que le aplica los efectos de CREATE/DROP de forma simulada, para validar un
script completo antes de ejecutar nada.
"""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field

from core.types import TipoSQL, literal_sql, parsear_literal_sql, parsear_tipo

class _SinDefault:
    """Marca de 'columna sin DEFAULT' (distinta de DEFAULT NULL); sobrevive a deepcopy."""

    def __repr__(self) -> str:
        return "SIN_DEFAULT"

    def __copy__(self):
        return self

    def __deepcopy__(self, _memo):
        return self


SIN_DEFAULT = _SinDefault()


@dataclass
class Columna:
    nombre: str
    tipo: TipoSQL
    not_null: bool = False
    default: object = SIN_DEFAULT

    @property
    def tiene_default(self) -> bool:
        return self.default is not SIN_DEFAULT


@dataclass
class LlaveForanea:
    columna: str
    tabla_ref: str
    columna_ref: str


@dataclass
class Tabla:
    nombre: str
    columnas: list[Columna]
    primary_key: list[str] = field(default_factory=list)
    uniques: list[list[str]] = field(default_factory=list)
    foraneas: list[LlaveForanea] = field(default_factory=list)

    def columna(self, nombre: str) -> Columna | None:
        return next((c for c in self.columnas if c.nombre == nombre), None)

    @property
    def nombres(self) -> list[str]:
        return [c.nombre for c in self.columnas]

    def es_unica(self, columna: str) -> bool:
        """La columna sola es PRIMARY KEY o UNIQUE (requisito para ser referenciada)."""
        return self.primary_key == [columna] or [columna] in self.uniques


@dataclass
class Indice:
    nombre: str
    tabla: str
    columna: str
    unico: bool = False


@dataclass
class Catalog:
    tablas: dict[str, Tabla] = field(default_factory=dict)
    indices: dict[str, Indice] = field(default_factory=dict)

    def copia(self) -> "Catalog":
        return copy.deepcopy(self)

    def tabla(self, nombre: str) -> Tabla | None:
        return self.tablas.get(nombre)

    def indices_de(self, tabla: str) -> list[Indice]:
        return [i for i in self.indices.values() if i.tabla == tabla]

    def indice_sobre(self, tabla: str, columna: str) -> Indice | None:
        return next((i for i in self.indices.values() if i.tabla == tabla and i.columna == columna), None)

    def referencias_a(self, tabla: str) -> list[tuple[str, LlaveForanea]]:
        """(tabla_hija, fk) de cada llave foranea que apunta a `tabla` desde OTRA tabla."""
        return [(t.nombre, fk) for t in self.tablas.values() for fk in t.foraneas
                if fk.tabla_ref == tabla and t.nombre != tabla]

    def referencias_entrantes(self, tabla: str) -> list[tuple[str, LlaveForanea]]:
        """Igual que referencias_a pero incluye las auto-referencias."""
        return [(t.nombre, fk) for t in self.tablas.values() for fk in t.foraneas if fk.tabla_ref == tabla]

    def eliminar_tabla(self, nombre: str) -> None:
        self.tablas.pop(nombre, None)
        for idx in [i for i in self.indices.values() if i.tabla == nombre]:
            del self.indices[idx.nombre]

    # ------------------------------------------------------------------
    # metadata.txt
    # ------------------------------------------------------------------

    def a_texto(self) -> str:
        lineas = ["# metadata.txt - catálogo de la base de datos (lo escribe el intérprete SQL)", ""]
        for t in self.tablas.values():
            lineas.append(f"TABLA {t.nombre}")
            for c in t.columnas:
                linea = f"  COLUMNA {c.nombre} {c.tipo} {'NOT NULL' if c.not_null else 'NULL'}"
                if c.tiene_default:
                    linea += f" DEFAULT {literal_sql(c.default)}"
                lineas.append(linea)
            if t.primary_key:
                lineas.append(f"  PRIMARY KEY ({', '.join(t.primary_key)})")
            for u in t.uniques:
                lineas.append(f"  UNIQUE ({', '.join(u)})")
            for fk in t.foraneas:
                lineas.append(f"  FOREIGN KEY ({fk.columna}) REFERENCES {fk.tabla_ref} ({fk.columna_ref})")
            lineas.append("FIN")
            lineas.append("")
        for i in self.indices.values():
            lineas.append(f"INDICE {'UNICO ' if i.unico else ''}{i.nombre} ON {i.tabla} ({i.columna})")
        return "\n".join(lineas).rstrip() + "\n"

    @classmethod
    def desde_texto(cls, texto: str) -> "Catalog":
        cat = cls()
        actual: Tabla | None = None
        for numero, cruda in enumerate(texto.splitlines(), start=1):
            linea = cruda.strip()
            if not linea or linea.startswith("#"):
                continue
            try:
                if linea.startswith("TABLA "):
                    actual = Tabla(linea.split()[1], [])
                    cat.tablas[actual.nombre] = actual
                elif linea == "FIN":
                    actual = None
                elif linea.startswith("COLUMNA ") and actual is not None:
                    actual.columnas.append(_parsear_columna(linea))
                elif linea.startswith("PRIMARY KEY") and actual is not None:
                    actual.primary_key = _lista_parentesis(linea)
                elif linea.startswith("UNIQUE") and actual is not None:
                    actual.uniques.append(_lista_parentesis(linea))
                elif linea.startswith("FOREIGN KEY") and actual is not None:
                    m = re.match(r"FOREIGN KEY \((\w+)\) REFERENCES (\w+) \((\w+)\)$", linea)
                    actual.foraneas.append(LlaveForanea(*m.groups()))
                elif linea.startswith("INDICE "):
                    m = re.match(r"INDICE (UNICO )?(\w+) ON (\w+) \((\w+)\)$", linea)
                    unico, nombre, tabla, columna = m.groups()
                    cat.indices[nombre] = Indice(nombre, tabla, columna, unico is not None)
                else:
                    raise ValueError("línea no reconocida")
            except Exception as error:  # noqa: BLE001 - se re-lanza con la linea
                raise ValueError(f"metadata.txt, línea {numero}: {cruda!r} ({error})") from error
        return cat


_RE_COLUMNA = re.compile(r"^COLUMNA (\w+) (\w+(?:\(\d+\))?) (NOT NULL|NULL)(?: DEFAULT (.+))?$")


def _parsear_columna(linea: str) -> Columna:
    m = _RE_COLUMNA.match(linea)
    if not m:
        raise ValueError("columna mal formada")
    nombre, tipo, nulo, default = m.groups()
    col = Columna(nombre, parsear_tipo(tipo), nulo == "NOT NULL")
    if default is not None:
        col.default = parsear_literal_sql(default)
    return col


def _lista_parentesis(linea: str) -> list[str]:
    dentro = linea[linea.index("(") + 1:linea.rindex(")")]
    return [x.strip() for x in dentro.split(",") if x.strip()]
