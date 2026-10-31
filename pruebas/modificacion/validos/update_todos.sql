-- @caso: UPDATE sin WHERE afecta todas las filas
-- @usar: universidad
-- @resultado: 38
UPDATE cursos SET creditos = creditos * 2;
SELECT SUM(creditos) FROM cursos;
