-- @caso: AND / OR con parentesis
-- @usar: universidad
-- @resultado: Ana López | Diego Ruiz | Elena Castro
SELECT nombre FROM estudiantes WHERE (carrera = 'Sistemas' OR carrera = 'Civil') AND edad < 21;
