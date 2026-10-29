"""
Base de datos = un directorio:

    database/
    |-- metadata.txt          catalogo (esquemas, tipos, restricciones, indices)
    |-- estudiantes.csv       registros: encabezado + una linea por registro
    |-- cursos.csv
    `-- indices/
        `-- idx_edad.idx      un archivo por indice

Esta clase es la UNICA que toca los archivos. El interprete le pide filas
(todas, o solo ciertas posiciones cuando usa un indice) y le entrega las
modificaciones ya validadas; aqui se escriben el CSV y se mantienen los
indices de la tabla.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path

from core.types import deserializar, serializar

from almacenamiento.catalog import Catalog, Indice, Tabla
from almacenamiento.indexes import ArchivoIndice

METADATA = "metadata.txt"
CARPETA_INDICES = "indices"


class Database:
    def __init__(self, ruta: str | Path):
        self.ruta = Path(ruta)
        self.ruta.mkdir(parents=True, exist_ok=True)
        self.catalogo = Catalog()
        self.recargar()

    # ------------------------------------------------------------------
    # rutas / catalogo
    # ------------------------------------------------------------------

    @property
    def nombre(self) -> str:
        return self.ruta.name

    def ruta_tabla(self, tabla: str) -> Path:
        return self.ruta / f"{tabla}.csv"

    def ruta_indice(self, indice: str) -> Path:
        return self.ruta / CARPETA_INDICES / f"{indice}.idx"

    def recargar(self) -> None:
        ruta = self.ruta / METADATA
        if ruta.exists():
            self.catalogo = Catalog.desde_texto(ruta.read_text(encoding="utf-8"))
        else:
            self.catalogo = Catalog()
            self.guardar_catalogo()

    def guardar_catalogo(self) -> None:
        (self.ruta / METADATA).write_text(self.catalogo.a_texto(), encoding="utf-8")

    # ------------------------------------------------------------------
    # DDL
    # ------------------------------------------------------------------

    def crear_tabla(self, tabla: Tabla) -> None:
        self.catalogo.tablas[tabla.nombre] = tabla
        self._escribir_csv(tabla, [])
        self.guardar_catalogo()

    def eliminar_tabla(self, nombre: str) -> None:
        for idx in self.catalogo.indices_de(nombre):
            self.ruta_indice(idx.nombre).unlink(missing_ok=True)
        self.ruta_tabla(nombre).unlink(missing_ok=True)
        self.catalogo.eliminar_tabla(nombre)
        self.guardar_catalogo()

    def crear_indice(self, definicion: Indice) -> ArchivoIndice:
        """Construye el indice con los datos actuales. ValueError si es UNIQUE y hay duplicados."""
        tabla = self.catalogo.tabla(definicion.tabla)
        valores = [fila[definicion.columna] for fila in self.leer_tabla(definicion.tabla)]
        indice = ArchivoIndice.construir(definicion, tabla.columna(definicion.columna).tipo, valores)
        if definicion.unico:
            repetida = next((k for k, pos in indice.entradas.items() if len(pos) > 1), None)
            if repetida is not None:
                raise ValueError(repetida)
        indice.guardar(self.ruta_indice(definicion.nombre))
        self.catalogo.indices[definicion.nombre] = definicion
        self.guardar_catalogo()
        return indice

    def eliminar_indice(self, nombre: str) -> None:
        self.ruta_indice(nombre).unlink(missing_ok=True)
        self.catalogo.indices.pop(nombre, None)
        self.guardar_catalogo()

    def indice(self, nombre: str) -> ArchivoIndice:
        definicion = self.catalogo.indices[nombre]
        tipo = self.catalogo.tabla(definicion.tabla).columna(definicion.columna).tipo
        ruta = self.ruta_indice(nombre)
        if not ruta.exists():  # se borro a mano: se reconstruye
            valores = [fila[definicion.columna] for fila in self.leer_tabla(definicion.tabla)]
            indice = ArchivoIndice.construir(definicion, tipo, valores)
            indice.guardar(ruta)
            return indice
        return ArchivoIndice.cargar(ruta, definicion, tipo)

    # ------------------------------------------------------------------
    # lectura
    # ------------------------------------------------------------------

    def _lector(self, tabla: Tabla):
        ruta = self.ruta_tabla(tabla.nombre)
        if not ruta.exists():
            self._escribir_csv(tabla, [])
        with open(ruta, encoding="utf-8", newline="") as archivo:
            lector = csv.reader(archivo)
            encabezado = next(lector, None) or tabla.nombres
            tipos = [tabla.columna(c).tipo if tabla.columna(c) else None for c in encabezado]
            yield encabezado, tipos
            yield from lector

    def _decodificar(self, tabla: Tabla, encabezado, tipos, registro) -> dict:
        fila = dict.fromkeys(tabla.nombres)
        for nombre, tipo, texto in zip(encabezado, tipos, registro):
            if tipo is not None:
                fila[nombre] = deserializar(texto, tipo)
        return fila

    def leer_tabla(self, nombre: str) -> list[dict]:
        tabla = self.catalogo.tabla(nombre)
        lector = self._lector(tabla)
        encabezado, tipos = next(lector)
        return [self._decodificar(tabla, encabezado, tipos, r) for r in lector if r]

    def leer_posiciones(self, nombre: str, posiciones: list[int]) -> list[tuple[int, dict]]:
        """Solo decodifica los registros pedidos (los que devolvio un indice)."""
        buscadas = set(posiciones)
        if not buscadas:
            return []
        tabla = self.catalogo.tabla(nombre)
        lector = self._lector(tabla)
        encabezado, tipos = next(lector)
        encontradas: dict[int, dict] = {}
        ultima = max(buscadas)
        for pos, registro in enumerate(r for r in lector if r):
            if pos in buscadas:
                encontradas[pos] = self._decodificar(tabla, encabezado, tipos, registro)
            if pos >= ultima:
                break
        return [(p, encontradas[p]) for p in sorted(buscadas) if p in encontradas]

    def contar(self, nombre: str) -> int:
        lector = self._lector(self.catalogo.tabla(nombre))
        next(lector)
        return sum(1 for r in lector if r)

    # ------------------------------------------------------------------
    # escritura (las filas ya vienen validadas por el interprete)
    # ------------------------------------------------------------------

    def _linea(self, tabla: Tabla, fila: dict) -> str:
        buffer = io.StringIO()
        csv.writer(buffer, lineterminator="\n").writerow([serializar(fila[c]) for c in tabla.nombres])
        return buffer.getvalue()

    def _escribir_csv(self, tabla: Tabla, filas: list[dict]) -> None:
        with open(self.ruta_tabla(tabla.nombre), "w", encoding="utf-8", newline="") as archivo:
            csv.writer(archivo, lineterminator="\n").writerow(tabla.nombres)
            for fila in filas:
                archivo.write(self._linea(tabla, fila))

    def insertar(self, nombre: str, filas: list[dict]) -> None:
        tabla = self.catalogo.tabla(nombre)
        inicio = self.contar(nombre)
        with open(self.ruta_tabla(nombre), "a", encoding="utf-8", newline="") as archivo:
            for fila in filas:
                archivo.write(self._linea(tabla, fila))
        for definicion in self.catalogo.indices_de(nombre):
            indice = self.indice(definicion.nombre)
            for i, fila in enumerate(filas):
                indice.agregar(fila[definicion.columna], inicio + i)
            indice.guardar(self.ruta_indice(definicion.nombre))

    def actualizar(self, nombre: str, filas: list[dict], cambios: dict[int, tuple[dict, dict]]) -> None:
        """`filas` = tabla completa ya modificada; `cambios[pos] = (fila_vieja, fila_nueva)`."""
        tabla = self.catalogo.tabla(nombre)
        self._escribir_csv(tabla, filas)
        for definicion in self.catalogo.indices_de(nombre):
            col = definicion.columna
            if all(vieja[col] == nueva[col] for vieja, nueva in cambios.values()):
                continue
            indice = self.indice(definicion.nombre)
            for pos, (vieja, nueva) in cambios.items():
                if vieja[col] != nueva[col]:
                    indice.quitar(vieja[col], pos)
                    indice.agregar(nueva[col], pos)
            indice.guardar(self.ruta_indice(definicion.nombre))

    def eliminar(self, nombre: str, restantes: list[dict], eliminadas: dict[int, dict]) -> None:
        """`restantes` = filas que quedan (en orden); `eliminadas[pos] = fila borrada`."""
        tabla = self.catalogo.tabla(nombre)
        self._escribir_csv(tabla, restantes)
        posiciones = sorted(eliminadas)
        for definicion in self.catalogo.indices_de(nombre):
            indice = self.indice(definicion.nombre)
            for pos in posiciones:
                indice.quitar(eliminadas[pos][definicion.columna], pos)
            indice.remapear(posiciones)
            indice.guardar(self.ruta_indice(definicion.nombre))
