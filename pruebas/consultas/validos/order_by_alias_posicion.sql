-- @caso: ORDER BY por alias y por posicion
-- @usar: universidad
-- @resultado: Fernando Paz, 25 | Carla Méndez, 22 | Ana López, 20
SELECT nombre, edad AS e FROM estudiantes WHERE edad > 19 ORDER BY e DESC, 1;
