-- @caso: columna fuera de GROUP BY y de las agregaciones
-- @usar: universidad
-- @error: agregacion
SELECT carrera, nombre, COUNT(*) FROM estudiantes GROUP BY carrera;
