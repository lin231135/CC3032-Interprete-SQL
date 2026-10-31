-- @caso: CREATE UNIQUE INDEX
-- @usar: universidad
-- @resultado: 4
-- @contiene: metadata.txt :: INDICE UNICO idx_nombre ON cursos (nombre)
CREATE UNIQUE INDEX idx_nombre ON cursos (nombre);
SELECT id FROM cursos WHERE nombre = 'Cálculo';
