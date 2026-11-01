# IDE del interprete SQL: editor, cargar/guardar .sql, "Ejecutar" y "Analizar"
# (ANTLR + AST + analisis semantico + interprete sobre archivos), paneles de
# resultados, mensajes/plan, problemas, tokens, arbol sintactico, AST y
# bateria de pruebas.

from ide.app import SQLIDE, main

__all__ = ["SQLIDE", "main"]
