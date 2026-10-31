-- @caso: IN (lista) y BETWEEN sobre una columna indexada
-- @usar: universidad
-- @resultado: 2, 3
-- @plan: [edad IN (16, 25)]
-- @plan: [edad BETWEEN 19 AND 22]
CREATE INDEX idx_edad ON estudiantes (edad);
SELECT (SELECT COUNT(*) FROM estudiantes WHERE edad IN (16, 25)),
       (SELECT COUNT(*) FROM estudiantes WHERE edad BETWEEN 19 AND 22);
