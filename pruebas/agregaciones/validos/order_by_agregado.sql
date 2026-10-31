-- @caso: ORDER BY una agregacion que no esta en el SELECT
-- @usar: universidad
-- @resultado: 3
SELECT curso_id FROM inscripciones GROUP BY curso_id ORDER BY COUNT(*) DESC, curso_id LIMIT 1;
