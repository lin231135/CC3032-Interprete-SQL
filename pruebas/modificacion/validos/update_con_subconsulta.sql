-- @caso: UPDATE con subconsulta escalar en el WHERE
-- @usar: universidad
-- @resultado: 88.5
UPDATE inscripciones SET nota = nota + 5 WHERE curso_id = (SELECT id FROM cursos WHERE nombre = 'Compiladores');
SELECT AVG(nota) FROM inscripciones WHERE curso_id = 1;
