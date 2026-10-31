-- @caso: correlacionada sobre la misma tabla (maximo por carrera)
-- @usar: universidad
-- @resultado: Bruno Díaz | Carla Méndez | Fernando Paz
SELECT e.nombre FROM estudiantes e
WHERE e.edad = (SELECT MAX(e2.edad) FROM estudiantes e2 WHERE e2.carrera = e.carrera)
ORDER BY e.nombre;
