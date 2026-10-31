-- @caso: EXISTS correlacionada
-- @usar: universidad
-- @resultado: Compiladores | Cálculo
SELECT c.nombre FROM cursos c
WHERE EXISTS (SELECT * FROM inscripciones i WHERE i.curso_id = c.id AND i.nota > 90);
