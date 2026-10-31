-- @caso: 18 < edad (valor a la izquierda) tambien usa el indice
-- @usar: universidad
-- @resultado: 4
-- @plan: Índice idx_edad
CREATE INDEX idx_edad ON estudiantes (edad);
SELECT COUNT(*) FROM estudiantes WHERE 18 < edad;
