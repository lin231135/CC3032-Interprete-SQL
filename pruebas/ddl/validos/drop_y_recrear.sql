-- @caso: el analisis simula el catalogo: DROP y CREATE de la misma tabla en un script
-- @columnas: b
-- @resultado: hola
CREATE TABLE t (a INT);
DROP TABLE t;
CREATE TABLE t (b VARCHAR(10));
INSERT INTO t VALUES ('hola');
SELECT * FROM t;
