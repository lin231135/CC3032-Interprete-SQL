-- @caso: con un error semantico no se ejecuta ninguna sentencia (ni las anteriores)
-- @error: tabla
CREATE TABLE t (a INT);
INSERT INTO fantasma VALUES (1);
