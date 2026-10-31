-- @caso: INNER JOIN de tres tablas
-- @usar: universidad
-- @resultado: Ana López, Compiladores | Carla Méndez, Compiladores | Elena Castro, Compiladores
-- @plan: Hash join
SELECT e.nombre, c.nombre
FROM inscripciones i
INNER JOIN estudiantes e ON e.id = i.estudiante_id
INNER JOIN cursos c ON c.id = i.curso_id
WHERE c.nombre = 'Compiladores'
ORDER BY e.nombre;
