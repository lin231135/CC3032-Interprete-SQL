# Batería de pruebas `.sql`

```
pruebas/<categoría>/{validos,invalidos}/<nombre>.sql
```

La batería la ejecuta `pruebas/runner.py` (también desde pytest, `tests/test_bateria.py`,
y desde el IDE con **Batería**, F7). Cada caso corre sobre una **base de datos
nueva en una carpeta temporal**, así que los casos son independientes entre sí y
no tocan `database/`.

```bash
python pruebas/runner.py            # imprime "N/N pasaron" y los fallos
python -m pytest tests/test_bateria.py -q
```

## Categorías

| Categoría | Qué prueba |
|---|---|
| `lexico_sintaxis` | tokens, mayúsculas, comentarios; errores léxicos y sintácticos |
| `ddl` | `CREATE TABLE` (tipos y restricciones en `metadata.txt`), `DROP TABLE`, `IF [NOT] EXISTS` |
| `insercion` | `INSERT` (DEFAULT, varias filas, `INSERT ... SELECT`, conversiones) y valores incorrectos |
| `restricciones` | `PRIMARY KEY`, `UNIQUE`, `NOT NULL`, `FOREIGN KEY` |
| `consultas` | `SELECT`, `WHERE`, `AND/OR/NOT`, `NULL`, `LIKE`, `IN`, `BETWEEN`, fechas, `ORDER BY`, `DISTINCT`, `LIMIT` |
| `modificacion` | `UPDATE` y `DELETE` |
| `joins` | `INNER`, `LEFT` y `CROSS JOIN`, autojoin, ambigüedad |
| `agregaciones` | `COUNT/SUM/AVG/MIN/MAX`, `GROUP BY`, `HAVING` |
| `indices` | `CREATE/DROP INDEX`, uso del índice (plan) y su mantenimiento en `INSERT/UPDATE/DELETE` |
| `subconsultas` | `IN`, `NOT IN`, `EXISTS`, `NOT EXISTS`, escalares, correlacionadas y anidadas |
| `generales` | scripts completos; varios errores reportados a la vez |
| `bases/` | datos compartidos (no son casos): `universidad.sql` |
| `demo/` | scripts para la presentación (fuera de la batería; `tests/test_bateria.py` los corre en orden) |

## Cabecera de cada archivo

Comentarios `--` al inicio del archivo:

```sql
-- @caso: descripción corta                       (obligatoria)
-- @usar: universidad                             (ejecuta antes pruebas/bases/universidad.sql)
-- @error: categoria                              (inválidos; una o más)
-- @columnas: a, b                                (válidos: columnas del último SELECT)
-- @filas: N                                      (válidos: cantidad de filas del último SELECT)
-- @resultado: v1, v2 | v3, v4                    (válidos: filas exactas del último SELECT, en orden)
-- @plan: texto                                   (válidos: el plan de alguna sentencia contiene el texto)
-- @no_plan: texto                                (válidos: ningún plan lo contiene)
-- @existe: ruta / @no_existe: ruta               (válidos: archivo dentro de la carpeta de la base)
-- @contiene: ruta :: texto                       (válidos: ese archivo de la base contiene el texto)
```

Los valores de `@resultado` se escriben como los muestra el intérprete:
`NULL`, `TRUE`/`FALSE`, `3.0`, `2024-01-15`.

**`validos/`** exige 0 errores (de análisis y de ejecución) y que se cumplan todas
las directivas. **`invalidos/`** exige al menos un error y que aparezcan **todas**
las categorías de `@error` (ver la tabla de categorías en
[`docs/Lenguaje_SQL.md`](../docs/Lenguaje_SQL.md#4-errores)).
