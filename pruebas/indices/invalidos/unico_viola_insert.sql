-- @caso: INSERT que repite un valor de un UNIQUE INDEX
-- @usar: universidad
-- @error: restriccion
CREATE UNIQUE INDEX idx_nombre ON estudiantes (nombre);
INSERT INTO estudiantes (id, nombre) VALUES (9, 'Ana López');
