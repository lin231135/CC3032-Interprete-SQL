-- @caso: subconsulta en HAVING
-- @usar: universidad
-- @resultado: Civil | Sistemas
SELECT carrera FROM estudiantes GROUP BY carrera HAVING AVG(edad) > (SELECT AVG(edad) FROM estudiantes)
ORDER BY carrera;
