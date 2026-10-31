-- @caso: subconsulta escalar que retorna mas de un registro (en ejecucion)
-- @usar: universidad
-- @error: subconsulta
SELECT nombre FROM estudiantes WHERE edad = (SELECT edad FROM estudiantes);
