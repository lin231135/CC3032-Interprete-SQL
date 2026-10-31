-- @caso: NULL <> 20 es desconocido: Hugo (edad NULL) no aparece
-- @usar: universidad
-- @resultado: 6
SELECT COUNT(*) FROM estudiantes WHERE edad <> 20;
