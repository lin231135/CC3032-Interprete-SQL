-- @caso: UNIQUE INDEX sobre una columna con valores repetidos
-- @usar: universidad
-- @error: restriccion
CREATE UNIQUE INDEX idx_carrera ON estudiantes (carrera);
