-- @caso: agregacion sobre un JOIN, HAVING y ORDER BY por alias
-- @usar: universidad
-- @resultado: Carla Méndez, 91.5 | Fernando Paz, 91.0
SELECT e.nombre, AVG(i.nota) AS promedio
FROM estudiantes e JOIN inscripciones i ON i.estudiante_id = e.id
GROUP BY e.nombre
HAVING AVG(i.nota) >= 85
ORDER BY promedio DESC;
