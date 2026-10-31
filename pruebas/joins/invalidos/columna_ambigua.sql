-- @caso: columna que existe en dos tablas del FROM
-- @usar: universidad
-- @error: referencia
SELECT nombre FROM estudiantes e JOIN cursos c ON e.id = c.id;
