-- @caso: numeros negativos y textos con comas y barras se guardan bien en el CSV
-- @resultado: -5, a;b | 7, x\y
-- @contiene: t.csv :: x\\y
CREATE TABLE t (n INT, s VARCHAR(10));
INSERT INTO t VALUES (-5, 'a;b'), (7, 'x\y');
SELECT n, s FROM t;
