-- 5. Subconsultas: IN / NOT IN, EXISTS / NOT EXISTS y escalares.

-- ejemplo del enunciado
SELECT nombre
FROM estudiantes
WHERE id IN (SELECT estudiante_id
             FROM inscripciones
             WHERE curso_id = 3);

SELECT nombre FROM estudiantes
WHERE id NOT IN (SELECT estudiante_id FROM inscripciones);

-- correlacionada: cursos con alguna nota mayor a 90
SELECT c.nombre FROM cursos c
WHERE EXISTS (SELECT * FROM inscripciones i WHERE i.curso_id = c.id AND i.nota > 90);

SELECT nombre FROM cursos c
WHERE NOT EXISTS (SELECT 1 FROM inscripciones i WHERE i.curso_id = c.id);

-- escalar en una comparación
SELECT nombre, edad FROM estudiantes
WHERE edad > (SELECT AVG(edad) FROM estudiantes);

-- escalar correlacionada en el SELECT
SELECT e.nombre,
       (SELECT COUNT(*) FROM inscripciones i WHERE i.estudiante_id = e.id) AS cursos,
       (SELECT MAX(i.nota) FROM inscripciones i WHERE i.estudiante_id = e.id) AS mejor_nota
FROM estudiantes e
ORDER BY cursos DESC, e.nombre;
