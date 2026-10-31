-- @caso: dos indices sobre la misma columna
-- @usar: universidad
-- @error: indice
CREATE INDEX idx_a ON estudiantes (edad);
CREATE INDEX idx_b ON estudiantes (edad);
