-- @caso: subconsulta escalar con mas de una columna
-- @usar: universidad
-- @error: subconsulta
SELECT nombre FROM estudiantes WHERE edad = (SELECT id, creditos FROM cursos);
