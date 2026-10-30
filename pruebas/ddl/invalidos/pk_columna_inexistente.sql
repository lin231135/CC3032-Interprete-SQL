-- @caso: PRIMARY KEY (x) sobre una columna que no existe
-- @error: columna
CREATE TABLE t (a INT, PRIMARY KEY (x));
