"""Resultado de ejecutar UNA sentencia (lo muestran el IDE y la CLI)."""

from __future__ import annotations

from dataclasses import dataclass, field

from core.errors import SQLError
from core.types import formatear


@dataclass
class ResultadoSentencia:
    numero: int                 # 1, 2, ... dentro del script
    tipo: str                   # SELECT, INSERT, CREATE TABLE...
    texto: str                  # SQL de la sentencia
    linea: int
    columnas: list[str] | None = None   # solo SELECT
    tipos: list[str] | None = None
    filas: list[tuple] | None = None
    mensaje: str = ""
    plan: list[str] = field(default_factory=list)  # como se accedio a los datos (indices, recorridos)
    afectadas: int = 0
    tiempo_ms: float = 0.0
    error: SQLError | None = None

    @property
    def ok(self) -> bool:
        return self.error is None

    @property
    def es_consulta(self) -> bool:
        return self.columnas is not None

    def filas_texto(self) -> list[list[str]]:
        return [[formatear(v) for v in fila] for fila in (self.filas or [])]

    def como_tabla(self, max_filas: int = 200) -> str:
        """Tabla en texto plano (CLI y pestana de mensajes)."""
        if not self.es_consulta:
            return self.mensaje
        encabezado = list(self.columnas)
        cuerpo = self.filas_texto()[:max_filas]
        anchos = [max([len(h)] + [len(f[i]) for f in cuerpo]) for i, h in enumerate(encabezado)]
        sep = "+" + "+".join("-" * (a + 2) for a in anchos) + "+"

        def linea(valores):
            return "| " + " | ".join(v.ljust(a) for v, a in zip(valores, anchos)) + " |"

        partes = [sep, linea(encabezado), sep, *[linea(f) for f in cuerpo], sep]
        total = len(self.filas or [])
        partes.append(f"{total} fila(s)" + (f" (se muestran {max_filas})" if total > max_filas else ""))
        return "\n".join(partes)
