-- @caso: columnas omitidas toman su DEFAULT o NULL
-- @usar: universidad
-- @resultado: Sistemas, TRUE, NULL
INSERT INTO estudiantes (id, nombre) VALUES (9, 'Iván');
SELECT carrera, activo, edad FROM estudiantes WHERE id = 9;
