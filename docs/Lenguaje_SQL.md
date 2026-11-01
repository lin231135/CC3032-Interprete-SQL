# Lenguaje SQL aceptado

La gramática completa está en [`grammar/SQL.g4`](../grammar/SQL.g4). Las
palabras reservadas no distinguen mayúsculas (`select` = `SELECT`); los nombres
de tablas, columnas, alias e índices se normalizan a minúsculas. Las sentencias
se separan con `;` (el último es opcional). Comentarios: `-- hasta fin de línea`
y `/* bloque */`.

## 1. Sentencias

```sql
CREATE TABLE [IF NOT EXISTS] t (
    col TIPO [PRIMARY KEY] [NOT NULL | NULL] [UNIQUE] [DEFAULT literal] [REFERENCES t2(col2)],
    ...,
    [PRIMARY KEY (c1, c2, ...)],
    [UNIQUE (c1, ...)],
    [FOREIGN KEY (c) REFERENCES t2 (c2)]
);
DROP TABLE [IF EXISTS] t;
CREATE [UNIQUE] INDEX nombre ON t (col);
DROP INDEX [IF EXISTS] nombre;

INSERT INTO t [(c1, c2, ...)] VALUES (e1, e2, ...), (...);
INSERT INTO t [(c1, c2, ...)] SELECT ...;
UPDATE t SET c1 = e1, c2 = e2 [WHERE condición];
DELETE FROM t [WHERE condición];

SELECT [DISTINCT] * | t.* | expr [[AS] alias], ...
[FROM t1 [[AS] a1]
      [, t2 [a2]]                                   -- producto cartesiano
      [CROSS JOIN t3 [a3]]
      [[INNER] JOIN t4 [a4] ON condición]
      [LEFT [OUTER] JOIN t5 [a5] ON condición] ...]
[WHERE condición]
[GROUP BY expr, ...]
[HAVING condición]
[ORDER BY expr | alias | posición [ASC | DESC], ...]
[LIMIT n [OFFSET m]];
```

## 2. Tipos

| Tipo | Valores | Literal |
|---|---|---|
| `INT` / `INTEGER` | enteros | `42`, `-7` |
| `FLOAT` | punto flotante | `3.5`, `.5`, `10.` |
| `VARCHAR(n)` | texto de hasta `n` caracteres | `'texto'`, `'it''s'` |
| `BOOLEAN` | `TRUE`, `FALSE` | `TRUE` |
| `DATE` | fechas `YYYY-MM-DD` válidas | `DATE '2024-02-29'` o `'2024-02-29'` donde se espera un `DATE` |
| — | `NULL` | `NULL` (compatible con cualquier tipo) |

Conversiones permitidas: un `INT` se puede guardar en una columna `FLOAT`; un
texto literal con formato `YYYY-MM-DD` se convierte a `DATE` al compararlo o
asignarlo a un `DATE` (si no es una fecha válida, p. ej. `'2024-02-30'`, es un
error semántico). No hay más conversiones implícitas: `edad = 'veinte'` es un
error de tipos.

## 3. Expresiones (de menor a mayor precedencia)

| Nivel | Operadores |
|---|---|
| 1 | `OR` |
| 2 | `AND` |
| 3 | `NOT` |
| 4 | `= <> != < <= > >=`, `IS [NOT] NULL`, `[NOT] BETWEEN a AND b`, `[NOT] LIKE`, `[NOT] IN (...)`, `EXISTS (...)` |
| 5 | `\|\|` (concatenación; convierte números y fechas a texto) |
| 6 | `+ -` |
| 7 | `* / %` |
| 8 | `-` unario |
| 9 | literales, columnas (`col` o `t.col`), `( expr )`, `( SELECT ... )`, `COUNT(*)`, `COUNT/SUM/AVG/MIN/MAX([DISTINCT] expr)` |

### Semántica

- **NULL** (lógica de tres valores): cualquier comparación o aritmética con
  `NULL` da `NULL` (desconocido). `WHERE`, `ON` y `HAVING` conservan solo las
  filas cuya condición es `TRUE`. `NULL AND FALSE = FALSE`, `NULL OR TRUE = TRUE`.
  `x IN (…, NULL)` es `NULL` si `x` no está en la lista.
- **Aritmética**: `INT op INT` da `INT`, salvo `/`, que siempre da `FLOAT`
  (`7 / 2 = 3.5`). `%` conserva el signo del dividendo. Dividir entre cero es un
  error de ejecución.
- **LIKE**: `%` = cualquier secuencia, `_` = un carácter; distingue mayúsculas.
- **Agregaciones**: ignoran los `NULL`. Sobre cero filas, `COUNT` da `0` y las demás
  `NULL`. `AVG` da `FLOAT`; `SUM` conserva el tipo. `MIN`/`MAX` funcionan con
  números, textos y fechas.
- **GROUP BY**: si hay `GROUP BY`, `HAVING` o alguna agregación, cada columna que
  se use fuera de una agregación (en `SELECT`, `HAVING` u `ORDER BY`) debe estar
  en el `GROUP BY`. Sin `GROUP BY`, toda la tabla es un solo grupo.
- **ORDER BY**: `NULL` va primero en orden ascendente (último en descendente). Se
  puede ordenar por alias del `SELECT`, por posición (`ORDER BY 2`) o por cualquier
  expresión, incluso agregaciones que no se proyectan.
- **Subconsultas**: las de `IN` y las escalares deben retornar exactamente una
  columna (error semántico). Una escalar sin registros vale `NULL`; con más de un
  registro es un error de ejecución. Pueden referirse a columnas de las consultas
  externas (correlacionadas); la consulta externa no ve las columnas internas.
- **JOIN**: la condición `ON` puede usar las tablas ya mencionadas a su izquierda.
  `LEFT JOIN` rellena con `NULL` las columnas de la derecha cuando no hay pareja.
- **UPDATE**: todas las expresiones de `SET` usan los valores **anteriores** de la fila.

## 4. Errores

Cada error tiene **fase**, **categoría**, **línea:columna** y mensaje. El
análisis semántico se hace sobre todo el script antes de ejecutar: si hay
cualquier error léxico, sintáctico o semántico **no se ejecuta ninguna
sentencia**. Un error de ejecución detiene el script en esa sentencia (la
sentencia no tiene efecto; las anteriores ya quedaron guardadas).

| Fase | Categoría | Ejemplos |
|---|---|---|
| Léxico | `lexico` | símbolo no reconocido (`#`, `@`), texto sin comilla de cierre |
| Sintáctico | `sintactico` | `SELECT nombre FROM WHERE ...`, falta `)`, falta `;` entre sentencias |
| Semántico | `tabla` | tabla inexistente, tabla duplicada, más de una `PRIMARY KEY` |
| | `columna` | columna inexistente, columna duplicada (en `CREATE`, `INSERT` o `SET`) |
| | `tipo` | tipos incompatibles en comparaciones, aritmética, `LIKE`, `SUM/AVG`, asignaciones; `WHERE` que no es `BOOLEAN` |
| | `valor` | cantidad de valores en `INSERT`, `NULL` en `NOT NULL`, texto más largo que `VARCHAR(n)`, fecha inválida, columna `NOT NULL` omitida |
| | `referencia` | columna ambigua, alias duplicado o inexistente, `ORDER BY` fuera de rango, FK a columna no única, `DROP TABLE` referenciada |
| | `indice` | índice inexistente o duplicado (por nombre o por columna) |
| | `subconsulta` | subconsulta escalar o de `IN` con más de una columna |
| | `agregacion` | agregación en `WHERE`/`ON`/`GROUP BY`/`SET`/`VALUES`, agregaciones anidadas, columna fuera del `GROUP BY` |
| Ejecución | `restriccion` | `PRIMARY KEY`/`UNIQUE` duplicada, `FOREIGN KEY` inexistente o referenciada, `NULL` calculado en `NOT NULL` |
| | `valor` | texto calculado más largo que `VARCHAR(n)` |
| | `subconsulta` | subconsulta escalar que retorna más de un registro |
| | `ejecucion` | división entre cero |

Los mensajes de ANTLR se traducen al español, por ejemplo
`Entrada inesperada ';'; se esperaba una expresión (columna, valor o subconsulta)`.
