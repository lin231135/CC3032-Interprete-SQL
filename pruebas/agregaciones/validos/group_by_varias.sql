-- @caso: GROUP BY con dos columnas
-- @usar: universidad
-- @resultado: Civil, TRUE, 2 | Industrial, TRUE, 2 | Sistemas, FALSE, 1 | Sistemas, TRUE, 3
SELECT carrera, activo, COUNT(*) FROM estudiantes GROUP BY carrera, activo ORDER BY carrera, activo;
