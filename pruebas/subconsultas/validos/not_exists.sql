-- @caso: NOT EXISTS
-- @usar: universidad
-- @resultado: Física
SELECT nombre FROM cursos c WHERE NOT EXISTS (SELECT 1 FROM inscripciones i WHERE i.curso_id = c.id);
