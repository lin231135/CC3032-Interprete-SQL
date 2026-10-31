"""
CLI del interprete SQL.

    python main.py                              abre el IDE
    python main.py script.sql                   ejecuta el script sobre database/
    python main.py script.sql --db otra_bd      ... sobre otra carpeta
    python main.py script.sql --check           solo analiza (lexico, sintactico, semantico)
    python main.py script.sql --tokens          + lista de tokens
    python main.py script.sql --ast             + AST en texto
    python main.py script.sql --plan            + plan de acceso (indices / recorridos)

Codigo de salida: 0 si todo fue bien, 1 si hubo errores.
"""

from __future__ import annotations

import sys

from almacenamiento.database import Database
from arbol.render import ast_texto
from driver import BD_POR_DEFECTO, analizar_archivo


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):  # la consola de Windows no siempre es UTF-8
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    banderas = {a for a in argv if a.startswith("--") and a != "--db"}
    posicionales = []
    ruta_bd = BD_POR_DEFECTO
    i = 0
    while i < len(argv):
        if argv[i] == "--db" and i + 1 < len(argv):
            ruta_bd = argv[i + 1]
            i += 2
            continue
        if not argv[i].startswith("--"):
            posicionales.append(argv[i])
        i += 1

    if not posicionales:
        from ide.app import main as lanzar_ide

        lanzar_ide()
        return 0

    db = Database(ruta_bd)
    resultado = analizar_archivo(posicionales[0], db, ejecutar="--check" not in banderas)

    if "--tokens" in banderas:
        print("== Tokens ==")
        for t in resultado.tokens:
            print(f"  {t.linea}:{t.columna:<4} {t.tipo:<12} {t.lexema}")
        print()
    if "--ast" in banderas and resultado.ast is not None:
        print("== AST ==")
        print(ast_texto(resultado.ast))
        print()

    for r in resultado.resultados:
        print(f"-- [{r.numero}] {r.tipo} (línea {r.linea}, {r.tiempo_ms:.1f} ms)")
        if r.ok:
            print(r.como_tabla() if r.es_consulta else r.mensaje)
        if "--plan" in banderas:
            for nota in r.plan:
                print(f"   plan: {nota}")
        print()

    if resultado.errores:
        print(f"Errores ({len(resultado.errores)}):")
        for error in resultado.errores:
            print(f"  {error}")
        return 1
    if "--check" in banderas:
        print(f"Análisis correcto: {len(resultado.ast.sentencias)} sentencia(s), 0 errores")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
