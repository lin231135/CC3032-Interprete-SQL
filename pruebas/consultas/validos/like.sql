-- @caso: LIKE con % y _
-- @usar: universidad
-- @resultado: Carla Méndez | Diego Ruiz
SELECT nombre FROM estudiantes WHERE nombre LIKE 'C%' OR nombre LIKE '_iego%';
