-- @caso: CREATE TABLE con los cinco tipos; el esquema queda en metadata.txt
-- @columnas: id, nombre, precio, disponible, creado
-- @filas: 0
-- @existe: productos.csv
-- @contiene: metadata.txt :: COLUMNA nombre VARCHAR(30) NOT NULL
-- @contiene: metadata.txt :: COLUMNA precio FLOAT NULL DEFAULT 0.0
-- @contiene: productos.csv :: id,nombre,precio,disponible,creado
CREATE TABLE productos (
    id INTEGER PRIMARY KEY,
    nombre VARCHAR(30) NOT NULL,
    precio FLOAT DEFAULT 0.0,
    disponible BOOLEAN,
    creado DATE
);
SELECT * FROM productos;
