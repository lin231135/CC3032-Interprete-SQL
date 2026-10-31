-- @caso: subconsulta escalar sin registros = NULL
-- @usar: universidad
-- @resultado: NULL
SELECT (SELECT nombre FROM cursos WHERE id = 99);
