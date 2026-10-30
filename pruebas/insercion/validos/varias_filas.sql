-- @caso: INSERT con varias filas en VALUES
-- @resultado: 3
CREATE TABLE t (a INT, b VARCHAR(5));
INSERT INTO t VALUES (1, 'a'), (2, 'b'), (3, NULL);
SELECT COUNT(*) FROM t;
