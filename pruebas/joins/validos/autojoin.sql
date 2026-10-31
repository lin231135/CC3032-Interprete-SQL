-- @caso: la misma tabla dos veces con distintos alias
-- @usar: universidad
-- @resultado: Bruno Díaz, Elena Castro
SELECT a.nombre, b.nombre FROM estudiantes a JOIN estudiantes b ON a.ingreso = b.ingreso AND a.id < b.id;
