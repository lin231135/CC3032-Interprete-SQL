-- @caso: INSERT agrega la entrada al indice
-- @usar: universidad
-- @resultado: Iván
-- @plan: Índice idx_edad actualizado (+1 entrada(s))
-- @contiene: indices/idx_edad.idx :: 30|8
CREATE INDEX idx_edad ON estudiantes (edad);
INSERT INTO estudiantes (id, nombre, edad) VALUES (9, 'Iván', 30);
SELECT nombre FROM estudiantes WHERE edad = 30;
