-- @caso: HAVING sin GROUP BY (un solo grupo) que no se cumple
-- @usar: universidad
-- @filas: 0
SELECT COUNT(*) FROM estudiantes HAVING COUNT(*) > 100;
