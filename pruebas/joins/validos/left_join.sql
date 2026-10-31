-- @caso: LEFT JOIN conserva los cursos sin inscripciones
-- @usar: universidad
-- @resultado: Bases de Datos, 3 | Compiladores, 3 | Cálculo, 3 | Estructuras de Datos, 4 | Física, 0
SELECT c.nombre, COUNT(i.estudiante_id) FROM cursos c LEFT JOIN inscripciones i ON i.curso_id = c.id
GROUP BY c.nombre ORDER BY c.nombre;
