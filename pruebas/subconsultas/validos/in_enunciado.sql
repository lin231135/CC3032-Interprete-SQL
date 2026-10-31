-- @caso: ejemplo del enunciado: IN con subconsulta
-- @usar: universidad
-- @resultado: Ana López | Bruno Díaz | Diego Ruiz | Elena Castro
SELECT nombre
FROM estudiantes
WHERE id IN (SELECT estudiante_id
             FROM inscripciones
             WHERE curso_id = 3);
