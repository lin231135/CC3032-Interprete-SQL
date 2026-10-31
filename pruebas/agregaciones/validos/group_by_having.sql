-- @caso: GROUP BY + HAVING
-- @usar: universidad
-- @columnas: carrera, n
-- @resultado: Sistemas, 4
SELECT carrera, COUNT(*) AS n FROM estudiantes GROUP BY carrera HAVING COUNT(*) > 2;
