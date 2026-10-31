-- @caso: subconsulta escalar en una comparacion
-- @usar: universidad
-- @resultado: Ana López | Carla Méndez | Fernando Paz
SELECT nombre FROM estudiantes WHERE edad > (SELECT AVG(edad) FROM estudiantes);
