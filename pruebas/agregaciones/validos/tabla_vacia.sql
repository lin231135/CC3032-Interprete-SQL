-- @caso: agregaciones sobre una tabla vacia: COUNT = 0, el resto NULL
-- @resultado: 0, NULL, NULL
CREATE TABLE v (x INT);
SELECT COUNT(*), SUM(x), MAX(x) FROM v;
