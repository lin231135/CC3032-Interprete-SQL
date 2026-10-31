-- @caso: subconsultas anidadas en dos niveles
-- @usar: universidad
-- @resultado: Ana López | Carla Méndez | Elena Castro
SELECT nombre FROM estudiantes
WHERE id IN (SELECT estudiante_id FROM inscripciones
             WHERE curso_id IN (SELECT id FROM cursos WHERE creditos >= 5));
