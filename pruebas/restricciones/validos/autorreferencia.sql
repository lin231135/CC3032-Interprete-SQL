-- @caso: FOREIGN KEY a la misma tabla
-- @resultado: Ana, NULL | Beto, Ana
CREATE TABLE emp (id INT PRIMARY KEY, nombre VARCHAR(10), jefe INT REFERENCES emp(id));
INSERT INTO emp VALUES (1, 'Ana', NULL), (2, 'Beto', 1);
SELECT e.nombre, j.nombre FROM emp e LEFT JOIN emp j ON j.id = e.jefe ORDER BY e.id;
