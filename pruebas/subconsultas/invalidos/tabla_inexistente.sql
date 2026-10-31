-- @caso: subconsulta sobre una tabla inexistente
-- @usar: universidad
-- @error: tabla
SELECT nombre FROM estudiantes WHERE id IN (SELECT id FROM alumnos);
