# Proyecto 2 — Intérprete SQL con almacenamiento en archivos

Construcción de Compiladores · UVG 2026

Intérprete de un subconjunto de **SQL** que analiza (léxico, sintáctico,
semántico) y ejecuta sentencias sobre su **propio** mecanismo de
almacenamiento: una base de datos es una carpeta con un `metadata.txt`, un
`.csv` por tabla y un archivo por índice. **No se usa ningún DBMS** (ni SQLite,
ni MySQL, ni PostgreSQL) para almacenar ni para ejecutar.

```
SQL → análisis léxico → análisis sintáctico → AST → análisis semántico → interpretación → archivos → resultado
       (ANTLR)            (ANTLR)              (arbol/)  (semantico/)        (interprete/)   (almacenamiento/)
```

| Entregable del enunciado | Dónde está |
|---|---|
| 1. Lexer y parser | `grammar/SQL.g4` → `generated/` (ANTLR 4.13.2) |
| 2. AST | `arbol/nodes.py` (nodos), `arbol/builder.py` (árbol sintáctico → AST) |
| 3. Análisis semántico y manejo de errores | `semantico/analyzer.py`, `core/errors.py` |
| 4. `CREATE`, `DROP` e `INSERT` | `interprete/executor.py`, `almacenamiento/` |
| 5. `SELECT`, `WHERE`, `UPDATE` y `DELETE` | `interprete/executor.py`, `interprete/evaluator.py` |
| 6. `JOIN`, agregaciones y `GROUP BY` | `interprete/executor.py`, `interprete/evaluator.py` |
| 7. Índices y subconsultas | `almacenamiento/indexes.py`, `interprete/executor.py` |
| 8. Integración: interfaz gráfica | `ide/app.py` (`python main.py`) |
| Almacenamiento en archivos | `almacenamiento/` · formato en [`docs/Almacenamiento.md`](docs/Almacenamiento.md) |
| Batería de pruebas | `pruebas/` (156 casos `.sql`), `tests/` (pytest) |

## Requisitos e instalación

- Python 3.11+
- (Opcional) Java, solo si se modifica la gramática y hay que regenerar el parser
- (Opcional) Graphviz (`dot` en el `PATH`) para ver el árbol sintáctico y el AST
  como imagen en el IDE; sin él se muestran como texto

```bash
pip install -r requirements.txt
```

El parser de ANTLR **ya viene generado** en `generated/` (versionado), así que
no hace falta Java para ejecutar el intérprete. Solo si se cambia
`grammar/SQL.g4`:

```bash
python build_grammar.py
```

## Cómo ejecutar

```bash
# IDE gráfico (usa la base de datos ./database; se crea si no existe)
python main.py

# Línea de comandos
python main.py script.sql                 # ejecuta el script sobre ./database
python main.py script.sql --db otra_bd    # ... sobre otra carpeta
python main.py script.sql --check         # solo analiza (léxico, sintáctico, semántico), no ejecuta
python main.py script.sql --tokens --ast  # además imprime los tokens y el AST
python main.py script.sql --plan          # además imprime cómo se accedió a los datos (índices)

# Batería de pruebas .sql (cada caso corre sobre una base temporal)
python pruebas/runner.py

# Todas las pruebas
python -m pytest -q
```

### IDE

Estilo oscuro tipo Visual Studio Code (mismo diseño que el IDE de Compiscript):
editor con resaltado de SQL (las tablas y columnas de la base se colorean),
numeración de líneas y errores marcados; a la izquierda el explorador de la
**base de datos** (tablas, columnas con PK/FK/UNIQUE e índices; doble clic en una
tabla muestra sus datos) y de los **scripts** de ejemplo y de prueba; abajo las
pestañas:

| Pestaña | Contenido |
|---|---|
| **Resultados** | lista de sentencias ejecutadas y, para cada `SELECT`, la tabla de resultados (clic en un encabezado para ordenar) |
| **Mensajes** | lo que hizo cada sentencia, su tiempo y su **plan** (recorrido completo, índice usado, hash join...) |
| **Problemas** | errores léxicos, sintácticos, semánticos y de ejecución con línea, columna, tipo y categoría (doble clic: ir a la línea) |
| **Tokens** | tipo, lexema, línea y columna de cada token |
| **Árbol sintáctico** | el *parse tree* de ANTLR |
| **AST** | el árbol de sintaxis abstracta, con el tipo inferido de cada expresión |
| **Batería** | resultado de `pruebas/runner.py` |

| Atajo | Acción |
|---|---|
| **F5** (o Ctrl+Enter) | Ejecutar el script (o **solo la selección**, si hay texto seleccionado) |
| **F6** | Solo analizar: tokens, árboles y errores, sin tocar la base de datos |
| **F7** | Correr la batería de pruebas |
| Ctrl+S / Ctrl+O | Guardar / abrir `.sql` |
| Ctrl+/ | Comentar o descomentar líneas (`--`) |
| Ctrl + rueda, Ctrl +/-, Ctrl+0 | Zoom de la letra del editor (en los árboles: Ctrl + rueda) |

El botón **Base de datos…** cambia la carpeta de trabajo. Los scripts de
`pruebas/demo/` (en orden: esquema y datos, consultas, joins y agregaciones,
índices, subconsultas, errores) sirven para la presentación.

## Ejemplo

```sql
CREATE TABLE estudiantes (id INT PRIMARY KEY, nombre VARCHAR(50) NOT NULL, edad INT);
INSERT INTO estudiantes VALUES (1, 'Ana', 20), (2, 'Bruno', 17), (3, 'Carla', 22);
CREATE INDEX idx_edad ON estudiantes (edad);

SELECT nombre
FROM estudiantes
WHERE edad >= 18;
```

```
$ python main.py ejemplo.sql --plan
...
-- [4] SELECT (línea 5, 0.4 ms)
+--------+
| nombre |
+--------+
| Ana    |
| Carla  |
+--------+
2 fila(s)
   plan: Índice idx_edad sobre estudiantes.edad  [edad >= 18] → 2 registro(s) leído(s)
```

y en la carpeta de la base quedan:

```
database/
|-- metadata.txt          TABLA estudiantes / COLUMNA id INT NOT NULL / ... / INDICE idx_edad ON estudiantes (edad)
|-- estudiantes.csv       id,nombre,edad
|                         1,Ana,20 ...
`-- indices/
    `-- idx_edad.idx      17|1
                          20|0
                          22|2
```

## Qué soporta

- **Tipos**: `INT` (o `INTEGER`), `FLOAT`, `VARCHAR(n)`, `BOOLEAN`, `DATE` (`YYYY-MM-DD`).
- **DDL**: `CREATE TABLE [IF NOT EXISTS]` con `PRIMARY KEY` (de columna o compuesta),
  `NOT NULL`, `UNIQUE`, `DEFAULT`, `REFERENCES` / `FOREIGN KEY`; `DROP TABLE [IF EXISTS]`;
  `CREATE [UNIQUE] INDEX`; `DROP INDEX [IF EXISTS]`.
- **DML**: `INSERT` (varias filas, lista de columnas, `INSERT ... SELECT`), `UPDATE`, `DELETE`.
- **Consultas**: `SELECT [DISTINCT]`, `*` y `t.*`, alias, `FROM` con varias tablas,
  `[INNER] JOIN`, `LEFT [OUTER] JOIN`, `CROSS JOIN`, `WHERE`, `GROUP BY`, `HAVING`,
  `ORDER BY` (expresiones, alias o posición, `ASC`/`DESC`), `LIMIT` / `OFFSET`.
- **Expresiones**: `AND`, `OR`, `NOT`, `= <> != < <= > >=`, `+ - * / %`, `||`,
  `IS [NOT] NULL`, `[NOT] BETWEEN`, `[NOT] LIKE`, `[NOT] IN (lista)`,
  `COUNT(*)`, `COUNT/SUM/AVG/MIN/MAX([DISTINCT] expr)`.
- **Subconsultas**: `[NOT] IN (SELECT ...)`, `[NOT] EXISTS (SELECT ...)` y escalares
  en comparaciones, en el `SELECT`, en `HAVING`, en `VALUES` o en `SET`; correlacionadas
  o no (las no correlacionadas se evalúan una sola vez).
- **Índices** sobre una columna, guardados en archivos, usados en `WHERE` (`=`, `IN`,
  `BETWEEN`, `<`, `<=`, `>`, `>=`, `IN (SELECT ...)`) de `SELECT`, `UPDATE` y `DELETE`
  y en los `JOIN`; se mantienen al ejecutar `INSERT`, `UPDATE` y `DELETE`.
- **Errores** léxicos, sintácticos, semánticos y de ejecución con su tipo, categoría y
  ubicación (línea:columna). El análisis semántico revisa **todo** el script antes de
  ejecutar; si hay errores no se ejecuta nada.

## Documentación

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): arquitectura, contrato entre fases,
  estructura del repositorio y cómo se prueba.
- [`docs/Almacenamiento.md`](docs/Almacenamiento.md): formato de `metadata.txt`, de los
  `.csv` y de los índices; cómo se mantienen y cómo se usan.
- [`docs/Lenguaje_SQL.md`](docs/Lenguaje_SQL.md): gramática, tipos, semántica
  (NULL, conversiones, agregaciones, subconsultas) y lista de errores.
- [`pruebas/README.md`](pruebas/README.md): convención de la batería de pruebas.
