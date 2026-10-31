-- @caso: LIMIT ... OFFSET
-- @usar: universidad
-- @resultado: 3 | 4
SELECT id FROM estudiantes ORDER BY id LIMIT 2 OFFSET 2;
