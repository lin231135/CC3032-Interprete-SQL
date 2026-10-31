-- @caso: IN con una subconsulta de dos columnas
-- @usar: universidad
-- @error: subconsulta
SELECT nombre FROM estudiantes WHERE id IN (SELECT id, nombre FROM cursos);
