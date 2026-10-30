-- @caso: la columna referenciada debe ser PRIMARY KEY o UNIQUE
-- @usar: universidad
-- @error: referencia
CREATE TABLE t (x INT REFERENCES cursos(creditos));
