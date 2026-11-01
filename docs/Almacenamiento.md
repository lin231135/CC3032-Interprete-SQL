# Almacenamiento en archivos

Una base de datos es **una carpeta**. No se usa ningún DBMS: todo se lee y se
escribe con archivos de texto (UTF-8). La única clase que toca disco es
`almacenamiento/database.py` (`Database`).

```
database/
|-- metadata.txt          catálogo: tablas, columnas, tipos, restricciones e índices
|-- estudiantes.csv       una tabla = un CSV
|-- cursos.csv
|-- inscripciones.csv
`-- indices/
    |-- idx_edad.idx      un índice = un archivo
    `-- idx_insc_curso.idx
```

## 1. `metadata.txt` (esquemas, tipos y restricciones)

Formato propio, orientado a líneas y legible:

```
# metadata.txt - catálogo de la base de datos (lo escribe el intérprete SQL)

TABLA estudiantes
  COLUMNA id INT NOT NULL
  COLUMNA nombre VARCHAR(50) NOT NULL
  COLUMNA edad INT NULL
  COLUMNA carrera VARCHAR(30) NULL DEFAULT 'Sistemas'
  COLUMNA activo BOOLEAN NULL DEFAULT TRUE
  COLUMNA ingreso DATE NULL
  PRIMARY KEY (id)
FIN

TABLA inscripciones
  COLUMNA estudiante_id INT NOT NULL
  COLUMNA curso_id INT NOT NULL
  COLUMNA nota FLOAT NULL
  PRIMARY KEY (estudiante_id, curso_id)
  FOREIGN KEY (estudiante_id) REFERENCES estudiantes (id)
  FOREIGN KEY (curso_id) REFERENCES cursos (id)
FIN

INDICE idx_edad ON estudiantes (edad)
INDICE UNICO idx_nombre ON cursos (nombre)
```

| Línea | Significado |
|---|---|
| `TABLA t` … `FIN` | una tabla; el orden de las `COLUMNA` es el orden de las columnas |
| `COLUMNA c TIPO NULL\|NOT NULL [DEFAULT literal]` | tipo (`INT`, `FLOAT`, `VARCHAR(n)`, `BOOLEAN`, `DATE`), nulabilidad y valor por defecto como literal SQL (`18`, `'texto'`, `TRUE`, `DATE '2024-01-01'`, `NULL`) |
| `PRIMARY KEY (a, b)` | llave primaria (simple o compuesta); sus columnas son `NOT NULL` |
| `UNIQUE (a)` | restricción de unicidad (de columna o de tabla) |
| `FOREIGN KEY (c) REFERENCES t (c2)` | llave foránea; `t.c2` debe ser `PRIMARY KEY` o `UNIQUE` |
| `INDICE [UNICO] nombre ON t (c)` | índice sobre una columna |

Se reescribe completo en cada `CREATE`/`DROP`. Al abrir la base se lee y se
reconstruye el `Catalog` (`Catalog.desde_texto`); una línea inválida produce un
error que indica el número de línea.

## 2. `<tabla>.csv` (registros)

```
id,nombre,edad,carrera,activo,ingreso
1,Ana López,20,Sistemas,TRUE,2023-01-15
7,Gabriela Soto,16,Industrial,TRUE,\N
8,Hugo Morales,\N,Sistemas,TRUE,2022-01-12
```

- La primera línea es el encabezado (nombres de columna); luego **un registro por
  línea**, con el módulo `csv` de Python (los textos con comas o comillas se
  entrecomillan).
- `NULL` se escribe `\N`. `BOOLEAN` como `TRUE`/`FALSE`, `DATE` como `YYYY-MM-DD`,
  `FLOAT` con `repr` (sin pérdida).
- En los textos se escapan `\` → `\\`, salto de línea → `\n` y retorno → `\r`, para
  que cada registro ocupe exactamente una línea física.
- Al leer, cada valor se convierte al tipo de su columna según `metadata.txt`.
- La **posición** de un registro es su número de línea de datos (0 = primer registro).
  Los índices guardan posiciones.

`INSERT` agrega líneas al final; `UPDATE` y `DELETE` reescriben el archivo (con
el estado final ya validado).

## 3. `indices/<nombre>.idx` (índices)

```
# indice: idx_edad
# tabla: estudiantes
# columna: edad
# tipo: INT
# unico: NO
16|6
17|1
18|4
19|3
20|0
22|2
25|5
```

Cada línea es `clave|posición,posición,...`, ordenada por clave. Los `NULL` no se
indexan (una condición `col = valor` nunca es verdadera para un `NULL`). En
memoria (`ArchivoIndice`) es un diccionario clave → posiciones más la lista
ordenada de claves: igualdad en O(1) y rangos con búsqueda binaria.

### Cuándo se usa

Para la tabla base del `FROM` de cada `SELECT` (también en subconsultas) y para
`UPDATE`/`DELETE`, se toman los términos `AND` del `WHERE` y se busca uno de la
forma *columna indexada* `op` *valor que no depende de la fila*:

| Condición | Búsqueda en el índice |
|---|---|
| `col = v` (o `v = col`) | `buscar(v)` |
| `col IN (v1, v2, ...)` | unión de `buscar(vi)` |
| `col IN (SELECT ...)` no correlacionada | se evalúa la subconsulta y se buscan sus valores |
| `col BETWEEN a AND b` | rango cerrado |
| `col < v`, `<=`, `>`, `>=` | rango abierto o cerrado |

El "valor" puede ser una expresión constante o referirse a la consulta externa
(en una subconsulta correlacionada se evalúa una vez por cada fila externa). Si
hay varias candidatas se prefiere la igualdad, luego `IN`, luego `BETWEEN`,
luego los rangos. El índice devuelve las posiciones candidatas y **solo esos
registros** se leen del CSV y se evalúan; el `WHERE` completo se sigue
evaluando sobre ellos, por lo que el resultado es idéntico al de un recorrido
completo (esto lo verifica `tests/test_ejecucion.py`). Con `OR` no se usa índice.

En un `JOIN ... ON t.col = expr` donde `t` es la tabla que se une, si `t.col`
tiene índice se busca en él por cada fila de la izquierda; si no, se construye
una tabla hash temporal sobre `t.col`.

El plan de cada sentencia lo registra, por ejemplo:

```
Índice idx_edad sobre estudiantes.edad  [edad >= 18] → 5 registro(s) leído(s)
Recorrido completo de estudiantes → 8 registro(s)
Índice idx_insc_curso en JOIN con inscripciones  [i.curso_id = c.id]
```

### Mantenimiento

| Sentencia | Qué se hace en cada índice de la tabla |
|---|---|
| `INSERT` | se agrega (clave, nueva posición) por cada registro nuevo |
| `UPDATE` | si cambió la columna indexada: se quita (clave vieja, pos) y se agrega (clave nueva, pos) |
| `DELETE` | se quitan las entradas de los registros borrados y cada posición `p` restante pasa a `p - (registros borrados antes de p)` |
| `DROP TABLE` | se borran los archivos de sus índices |
| `CREATE INDEX` | se construye leyendo la tabla; si es `UNIQUE` y hay repetidos, es un error |

Si el archivo `.idx` de un índice registrado no existe (por ejemplo, se borró a
mano), se reconstruye desde los datos la próxima vez que se usa.

## 4. Restricciones

Se guardan en `metadata.txt` y se verifican en ejecución, **antes** de escribir:

| Restricción | Cuándo |
|---|---|
| `NOT NULL` | `INSERT`/`UPDATE` (un `NULL` literal se detecta ya en el análisis semántico) |
| `VARCHAR(n)`, tipo, fecha válida | `INSERT`/`UPDATE` (los literales, en el análisis semántico) |
| `PRIMARY KEY`, `UNIQUE`, índice `UNIQUE` | `INSERT`/`UPDATE` (también entre las filas del mismo `INSERT`) |
| `FOREIGN KEY` (hija → padre) | `INSERT`/`UPDATE` de la tabla hija |
| `FOREIGN KEY` (padre ← hija) | `UPDATE`/`DELETE` de la tabla padre (*restrict*); `DROP TABLE` de una tabla referenciada es un error semántico |

Cada sentencia es atómica: si una sola fila viola una restricción, no se escribe
ninguna.
