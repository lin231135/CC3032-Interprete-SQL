-- @caso: INSERT INTO ... SELECT
-- @usar: universidad
-- @resultado: Ana López | Carla Méndez | Fernando Paz
CREATE TABLE mayores (id INT PRIMARY KEY, nombre VARCHAR(50));
INSERT INTO mayores SELECT id, nombre FROM estudiantes WHERE edad >= 20;
SELECT nombre FROM mayores ORDER BY id;
