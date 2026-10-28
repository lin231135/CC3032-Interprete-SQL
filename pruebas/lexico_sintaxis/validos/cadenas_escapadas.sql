-- @caso: comilla escapada '' dentro de un texto
-- @resultado: it's
CREATE TABLE t (s VARCHAR(20));
INSERT INTO t VALUES ('it''s');
SELECT s FROM t;
