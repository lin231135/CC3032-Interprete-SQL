-- @caso: DROP INDEX borra el archivo; la consulta vuelve a recorrer la tabla
-- @usar: universidad
-- @resultado: Ana López
-- @no_existe: indices/idx_edad.idx
-- @no_plan: Índice idx_edad sobre
CREATE INDEX idx_edad ON estudiantes (edad);
DROP INDEX idx_edad;
SELECT nombre FROM estudiantes WHERE edad = 20;
