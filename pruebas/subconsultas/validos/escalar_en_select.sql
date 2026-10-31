-- @caso: subconsulta escalar correlacionada en el SELECT
-- @usar: universidad
-- @resultado: Ana López, 3 | Bruno Díaz, 2 | Carla Méndez, 2
SELECT nombre, (SELECT COUNT(*) FROM inscripciones i WHERE i.estudiante_id = e.id) AS cursos
FROM estudiantes e ORDER BY cursos DESC, nombre LIMIT 3;
