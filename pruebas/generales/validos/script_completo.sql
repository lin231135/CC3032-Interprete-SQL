-- @caso: crear, insertar, consultar, modificar y borrar en un solo script
-- @resultado: Lápiz, 3.0
CREATE TABLE productos (id INT PRIMARY KEY, nombre VARCHAR(20) NOT NULL, precio FLOAT);
INSERT INTO productos VALUES (1, 'Lápiz', 2.5), (2, 'Cuaderno', 10), (3, 'Borrador', 1);
UPDATE productos SET precio = precio + 0.5 WHERE precio < 5;
DELETE FROM productos WHERE nombre = 'Borrador';
CREATE INDEX idx_precio ON productos (precio);
SELECT nombre, precio FROM productos WHERE precio < 5;
