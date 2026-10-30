-- @caso: el texto calculado excede VARCHAR(n) (se detecta al ejecutar)
-- @error: valor
CREATE TABLE t (s VARCHAR(3));
INSERT INTO t VALUES ('ab' || 'cd');
