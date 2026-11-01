# Arquitectura del intérprete

Intérprete de un subconjunto de SQL que analiza y ejecuta sentencias sobre su
propio almacenamiento en archivos (sin ningún DBMS).

## 1. Flujo

```
                   script.sql
                        │
          ┌─────────────▼──────────────┐
    (1)   │ ANTLR  (grammar/SQL.g4)    │  lexer → tokens        errores LÉXICOS     (línea:columna)
          │                            │  parser → árbol sint.  errores SINTÁCTICOS (línea:columna)
          └─────────────┬──────────────┘
                 ¿hay errores? ── sí ──► se muestran; no se construye el AST
                        │ no
          ┌─────────────▼──────────────┐
    (2)   │ ASTBuilder (arbol/builder) │  ParseTree → AST (arbol/nodes.py): identificadores en
          └─────────────┬──────────────┘  minúsculas, literales ya convertidos, NOT EXISTS plegado
                        │ AST
          ┌─────────────▼──────────────┐
    (3)   │ SemanticAnalyzer           │  valida TODO el script contra una COPIA del catálogo
          │ (semantico/analyzer.py)    │  (CREATE/DROP se simulan) y ANOTA el AST:
          │                            │   · ColumnRef → (ref_alias, ref_nivel)   · expr.tipo
          │                            │   · Select.columnas_salida / agrupado / correlacionada
          └─────────────┬──────────────┘   · OrderItem.indice_salida
                 ¿hay errores? ── sí ──► se muestran TODOS; no se ejecuta ninguna sentencia
                        │ no (y se pidió ejecutar)
          ┌─────────────▼──────────────┐
    (4)   │ Ejecutor (interprete/)     │  sentencia por sentencia, cada una atómica:
          │   executor.py, evaluator.py│  calcula filas → verifica restricciones → escribe
          └─────────────┬──────────────┘  un error de ejecución detiene el script ahí
                        │ lee / escribe
          ┌─────────────▼──────────────┐
    (5)   │ Database (almacenamiento/) │  metadata.txt · <tabla>.csv · indices/<indice>.idx
          └─────────────┬──────────────┘
                        ▼
              ResultadoSentencia por sentencia (columnas, filas, mensaje, plan, tiempo, error)
```

`driver.analizar(sql, db, ejecutar)` es el **único** punto de entrada del
pipeline y devuelve un `Resultado` con todo lo que muestran el IDE y la CLI:
tokens, árbol sintáctico, AST, errores por fase y resultados por sentencia.

## 2. Contrato entre fases

| Fase | Recibe | Produce | Garantiza |
|---|---|---|---|
| ANTLR | texto | tokens, `ParseTree` | errores léxicos y sintácticos traducidos al español (`core/errors.traducir_mensaje_antlr`) |
| ASTBuilder | `ParseTree` sin errores | `Script` (lista de sentencias) | cada nodo tiene `linea`, `columna` y `texto` original |
| SemanticAnalyzer | AST + `Catalog` | AST anotado + errores | si no hay errores, toda `ColumnRef` está resuelta, todo tipo es compatible y toda subconsulta escalar/IN tiene una columna |
| Ejecutor | AST anotado sin errores + `Database` | `ResultadoSentencia`s | las restricciones (PK, UNIQUE, NOT NULL, FK, longitudes) se verifican **antes** de escribir |
| Database | filas ya validadas | archivos | es la única clase que toca disco; mantiene los índices |

### Por qué el análisis usa una copia del catálogo

Un script como `CREATE TABLE t (...); INSERT INTO t ...; SELECT ... FROM t;`
debe validarse completo antes de ejecutar la primera sentencia, pero `t` todavía
no existe en disco. El analizador trabaja sobre `catalogo.copia()` y aplica ahí
los efectos de cada `CREATE`/`DROP` (tabla o índice), así que cada sentencia se
valida contra el esquema que tendrá la base **en ese punto del script**. Lo que
no se puede saber sin los datos (llaves duplicadas, FK inexistentes, una
subconsulta escalar que retorna más de un registro, división entre cero) se
reporta en ejecución.

### Resolución de nombres (alcances)

Cada `SELECT` abre un `Alcance` con sus tablas del `FROM` (alias → esquema) y un
puntero al alcance de la consulta externa. Una columna sin calificar se busca en
el alcance actual; si está en más de una tabla es **ambigua**; si no está, se
busca en el alcance externo (subconsulta correlacionada). El analizador anota en
la `ColumnRef` el alias encontrado y el **nivel** (0 = esta consulta, 1 = la
externa...). El evaluador usa esa anotación directamente: sube `ref_nivel`
entornos y lee `fila[ref_alias][columna]`, sin volver a buscar nombres.

Si una `ColumnRef` apunta a un nivel externo, todas las consultas intermedias se
marcan `correlacionada`; las que no lo están se ejecutan una sola vez por
sentencia y su resultado se reutiliza.

## 3. Ejecución

- **SELECT**: `FROM` (tabla base, con índice si hay una condición aplicable) →
  `JOIN`s (índice de la tabla interna, *hash join* para igualdades o *nested
  loop*) → `WHERE` → agrupación (`GROUP BY` / agregaciones) → `HAVING` →
  proyección → `ORDER BY` (estable, por varias claves) → `DISTINCT` → `OFFSET` /
  `LIMIT`.
- **INSERT / UPDATE / DELETE**: se calcula el estado final de la tabla, se
  verifican las restricciones sobre ese estado (y las FK que apuntan a la tabla)
  y recién entonces se escribe el CSV y se actualizan los índices.
- Cada sentencia lleva un **plan** (lista de notas) que el IDE muestra: qué
  tablas se recorrieron completas, qué índice se usó y cuántos registros se
  leyeron, qué JOIN se hizo, qué índices se actualizaron.

Los detalles del formato y del uso de índices están en
[`Almacenamiento.md`](Almacenamiento.md); la semántica del lenguaje en
[`Lenguaje_SQL.md`](Lenguaje_SQL.md).

## 4. Estructura del repositorio

```
grammar/SQL.g4             gramática ANTLR (lexer + parser)
generated/                 lexer/parser/visitor generados (versionados)
build_grammar.py           regenera generated/ (requiere Java)
driver.py                  pipeline: analizar(sql, db, ejecutar) -> Resultado
main.py                    CLI; sin argumentos abre el IDE

core/
  errors.py                SQLError, fases y categorías, traducción de mensajes de ANTLR
  types.py                 TipoSQL, compatibilidad, conversión y serialización de valores
arbol/
  nodes.py                 nodos del AST (dataclasses) y recorridos genéricos
  builder.py               ASTBuilder: ParseTree -> AST
  render.py                árbol sintáctico y AST a PNG (Graphviz) o texto
semantico/
  analyzer.py              SemanticAnalyzer (alcances, tipos, agregaciones, catálogo simulado)
interprete/
  executor.py              ejecución de sentencias, planes de acceso, restricciones
  evaluator.py             evaluación de expresiones (lógica de tres valores, subconsultas)
  results.py               ResultadoSentencia
almacenamiento/
  catalog.py               Catalog / Tabla / Columna / Indice y metadata.txt
  database.py              Database: la carpeta de la base (CSV, índices, catálogo)
  indexes.py               ArchivoIndice: archivo .idx, búsquedas y mantenimiento
ide/app.py                 IDE (CustomTkinter + Tk)

pruebas/
  runner.py                batería de casos .sql (cada uno sobre una base temporal)
  bases/universidad.sql    datos que usan los casos con `-- @usar: universidad`
  demo/                    scripts para la presentación
  <categoría>/{validos,invalidos}/*.sql
tests/                     pytest: fases, almacenamiento, ejecución, CLI y la batería
docs/                      esta documentación
```

## 5. Cómo se prueba

```bash
python pruebas/runner.py     # 156 casos .sql: "N/N pasaron"
python -m pytest -q          # unitarias por fase + la batería + los demos
```

- `tests/test_lexer_parser.py`: tokens, posiciones, errores léxicos y sintácticos.
- `tests/test_ast.py`: forma del AST, precedencia, literales, texto original.
- `tests/test_semantico.py`: ubicación de errores, catálogo simulado, anotaciones.
- `tests/test_almacenamiento.py`: `metadata.txt` ida y vuelta, CSV, índices y remapeo.
- `tests/test_ejecucion.py`: atomicidad, detención del script, índices = recorrido,
  mantenimiento de índices.
- `tests/test_bateria.py`: un test por cada `.sql` de `pruebas/` y los demos en orden.
