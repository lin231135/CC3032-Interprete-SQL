-- 3. INNER JOIN, LEFT JOIN, COUNT/SUM/AVG/MIN/MAX, GROUP BY y HAVING.

SELECT e.nombre, c.nombre AS curso, i.nota
FROM inscripciones i
INNER JOIN estudiantes e ON e.id = i.estudiante_id
INNER JOIN cursos c ON c.id = i.curso_id
ORDER BY e.nombre, curso;

SELECT COUNT(*) AS estudiantes, COUNT(edad) AS con_edad, SUM(edad), AVG(edad), MIN(edad), MAX(edad)
FROM estudiantes;

SELECT carrera, COUNT(*) AS total, AVG(edad) AS edad_promedio
FROM estudiantes
GROUP BY carrera
HAVING COUNT(*) >= 2
ORDER BY total DESC;

-- cursos con su cantidad de inscritos (Física no tiene: aparece con 0 gracias al LEFT JOIN)
SELECT c.nombre, COUNT(i.estudiante_id) AS inscritos, AVG(i.nota) AS promedio
FROM cursos c
LEFT JOIN inscripciones i ON i.curso_id = c.id
GROUP BY c.nombre
ORDER BY inscritos DESC, c.nombre;
