-- @caso: HAVING con una columna que no esta agrupada
-- @usar: universidad
-- @error: agregacion
SELECT carrera FROM estudiantes GROUP BY carrera HAVING edad > 18;
