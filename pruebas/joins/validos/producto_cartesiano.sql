-- @caso: FROM con coma y CROSS JOIN
-- @usar: universidad
-- @resultado: 25, 25
SELECT (SELECT COUNT(*) FROM cursos, cursos c2), (SELECT COUNT(*) FROM cursos CROSS JOIN cursos c2);
