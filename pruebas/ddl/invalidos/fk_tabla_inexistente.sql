-- @caso: REFERENCES a una tabla que no existe
-- @error: tabla
CREATE TABLE t (x INT REFERENCES nada(id));
