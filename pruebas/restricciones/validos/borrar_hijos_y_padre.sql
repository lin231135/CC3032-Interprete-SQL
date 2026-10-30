-- @caso: primero se borran las referencias y luego el registro padre
-- @usar: universidad
-- @resultado: 4
DELETE FROM inscripciones WHERE curso_id = 1;
DELETE FROM cursos WHERE id = 1;
SELECT COUNT(*) FROM cursos;
