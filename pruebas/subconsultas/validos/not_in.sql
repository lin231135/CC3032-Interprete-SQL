-- @caso: NOT IN con subconsulta
-- @usar: universidad
-- @resultado: Gabriela Soto
SELECT nombre FROM estudiantes WHERE id NOT IN (SELECT estudiante_id FROM inscripciones);
