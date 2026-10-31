-- @caso: UPDATE mueve la entrada del indice a la nueva clave
-- @usar: universidad
-- @resultado: 0, Ana López
-- @contiene: indices/idx_edad.idx :: 40|0
CREATE INDEX idx_edad ON estudiantes (edad);
UPDATE estudiantes SET edad = 40 WHERE id = 1;
SELECT (SELECT COUNT(*) FROM estudiantes WHERE edad = 20), (SELECT nombre FROM estudiantes WHERE edad = 40);
