-- @caso: la consulta externa no ve las columnas de la subconsulta
-- @usar: universidad
-- @error: columna
SELECT nombre FROM cursos WHERE id IN (SELECT curso_id FROM inscripciones) AND nota > 80;
