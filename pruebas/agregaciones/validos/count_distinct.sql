-- @caso: COUNT(DISTINCT ...)
-- @usar: universidad
-- @resultado: 3, 6
SELECT COUNT(DISTINCT carrera), COUNT(DISTINCT ingreso) FROM estudiantes;
