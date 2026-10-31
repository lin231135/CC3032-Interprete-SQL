-- @caso: IN con tipos incompatibles
-- @usar: universidad
-- @error: tipo
SELECT nombre FROM estudiantes WHERE nombre IN (SELECT id FROM cursos);
