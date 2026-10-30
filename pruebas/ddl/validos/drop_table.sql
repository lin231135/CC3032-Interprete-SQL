-- @caso: DROP TABLE borra la tabla, su CSV y sus indices
-- @no_existe: temporal.csv
-- @no_existe: indices/idx_tmp.idx
CREATE TABLE temporal (a INT);
CREATE INDEX idx_tmp ON temporal (a);
INSERT INTO temporal VALUES (1), (2);
DROP TABLE temporal;
