-- @caso: dos indices con el mismo nombre
-- @usar: universidad
-- @error: indice
CREATE INDEX idx_a ON estudiantes (edad);
CREATE INDEX idx_a ON cursos (creditos);
