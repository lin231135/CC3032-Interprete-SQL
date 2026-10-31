-- @caso: UPDATE de varias columnas con WHERE (usa los valores anteriores)
-- @usar: universidad
-- @resultado: Diego Ruiz, 20, FALSE | Fernando Paz, 26, FALSE
UPDATE estudiantes SET edad = edad + 1, activo = FALSE WHERE carrera = 'Civil';
SELECT nombre, edad, activo FROM estudiantes WHERE carrera = 'Civil';
