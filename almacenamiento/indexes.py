"""
Indices sobre una columna, guardados en `indices/<nombre>.idx`.

Formato (una clave por linea, posiciones de registro separadas por coma):

    # indice: idx_edad
    # tabla: estudiantes
    # columna: edad
    # tipo: INT
    # unico: NO
    18|0,3,7
    20|1

La POSICION es el numero de registro (0 = primera fila de datos del CSV). Las
claves se escriben con core.types.serializar y se ordenan por valor; los NULL
no se indexan (un WHERE col = x nunca los selecciona). En memoria el indice
es un dict clave -> [posiciones] mas la lista ordenada de claves, para
resolver igualdades en O(1) y rangos con busqueda binaria.

Mantenimiento incremental (lo invoca almacenamiento/database.py):
  INSERT -> agregar(clave, nueva_posicion)
  UPDATE -> quitar(clave_vieja, pos) + agregar(clave_nueva, pos)
  DELETE -> quitar(...) de las filas borradas + remapear(): cada posicion p
            pasa a p - (cuantas filas borradas habia antes de p)
"""

from __future__ import annotations

import bisect
from pathlib import Path

from core.types import TipoSQL, deserializar, serializar

from almacenamiento.catalog import Indice


class ArchivoIndice:
    def __init__(self, definicion: Indice, tipo: TipoSQL, entradas: dict | None = None):
        self.definicion = definicion
        self.tipo = tipo
        self.entradas: dict[object, list[int]] = entradas or {}
        self._claves: list | None = None

    # ------------------------------------------------------------------
    # construccion / disco
    # ------------------------------------------------------------------

    @classmethod
    def construir(cls, definicion: Indice, tipo: TipoSQL, valores: list) -> "ArchivoIndice":
        """`valores[pos]` = valor de la columna indexada en el registro `pos`."""
        indice = cls(definicion, tipo)
        for pos, valor in enumerate(valores):
            indice.agregar(valor, pos)
        return indice

    @classmethod
    def cargar(cls, ruta: Path, definicion: Indice, tipo: TipoSQL) -> "ArchivoIndice":
        entradas: dict[object, list[int]] = {}
        for linea in ruta.read_text(encoding="utf-8").splitlines():
            if not linea or linea.startswith("#"):
                continue
            clave, _, posiciones = linea.rpartition("|")
            entradas[deserializar(clave, tipo)] = [int(p) for p in posiciones.split(",") if p]
        return cls(definicion, tipo, entradas)

    def guardar(self, ruta: Path) -> None:
        d = self.definicion
        lineas = [f"# indice: {d.nombre}", f"# tabla: {d.tabla}", f"# columna: {d.columna}",
                  f"# tipo: {self.tipo}", f"# unico: {'SI' if d.unico else 'NO'}"]
        for clave in self.claves_ordenadas():
            lineas.append(f"{serializar(clave)}|{','.join(map(str, self.entradas[clave]))}")
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text("\n".join(lineas) + "\n", encoding="utf-8")

    # ------------------------------------------------------------------
    # mantenimiento
    # ------------------------------------------------------------------

    def agregar(self, valor, pos: int) -> None:
        if valor is None:
            return
        lista = self.entradas.get(valor)
        if lista is None:
            self.entradas[valor] = [pos]
            self._claves = None
        else:
            bisect.insort(lista, pos)

    def quitar(self, valor, pos: int) -> None:
        if valor is None:
            return
        lista = self.entradas.get(valor)
        if lista is None:
            return
        try:
            lista.remove(pos)
        except ValueError:
            return
        if not lista:
            del self.entradas[valor]
            self._claves = None

    def remapear(self, eliminadas: list[int]) -> None:
        """Ajusta las posiciones despues de borrar los registros `eliminadas` (ordenadas)."""
        if not eliminadas:
            return
        for clave, lista in self.entradas.items():
            self.entradas[clave] = [p - bisect.bisect_left(eliminadas, p) for p in lista]

    # ------------------------------------------------------------------
    # busquedas
    # ------------------------------------------------------------------

    def claves_ordenadas(self) -> list:
        if self._claves is None:
            self._claves = sorted(self.entradas)
        return self._claves

    def buscar(self, valor) -> list[int]:
        if valor is None:
            return []
        return list(self.entradas.get(valor, ()))

    def buscar_varios(self, valores) -> list[int]:
        posiciones: set[int] = set()
        for v in valores:
            posiciones.update(self.buscar(v))
        return sorted(posiciones)

    def buscar_rango(self, desde=None, incluye_desde=True, hasta=None, incluye_hasta=True) -> list[int]:
        """Posiciones con desde <(=) clave <(=) hasta; None en un extremo = sin limite."""
        claves = self.claves_ordenadas()
        try:
            if desde is None:
                i = 0
            else:
                i = bisect.bisect_left(claves, desde) if incluye_desde else bisect.bisect_right(claves, desde)
            if hasta is None:
                j = len(claves)
            else:
                j = bisect.bisect_right(claves, hasta) if incluye_hasta else bisect.bisect_left(claves, hasta)
        except TypeError:
            return []
        posiciones: list[int] = []
        for clave in claves[i:j]:
            posiciones.extend(self.entradas[clave])
        return sorted(posiciones)

    def __len__(self) -> int:
        return len(self.entradas)
