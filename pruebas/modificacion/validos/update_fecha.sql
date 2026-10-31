-- @caso: UPDATE de una fecha con un texto
-- @usar: universidad
-- @resultado: Gabriela Soto
UPDATE estudiantes SET ingreso = '2025-01-01' WHERE ingreso IS NULL;
SELECT nombre FROM estudiantes WHERE ingreso > '2024-06-01';
