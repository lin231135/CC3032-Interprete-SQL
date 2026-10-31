-- @caso: con OR no se puede usar el indice (se recorre la tabla)
-- @usar: universidad
-- @resultado: Bruno Díaz | Gabriela Soto
-- @no_plan: Índice idx_edad sobre
CREATE INDEX idx_edad ON estudiantes (edad);
SELECT nombre FROM estudiantes WHERE edad = 16 OR edad = 17;
