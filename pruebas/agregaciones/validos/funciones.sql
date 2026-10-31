-- @caso: COUNT(*), COUNT(col), SUM, AVG, MIN, MAX (los NULL se ignoran)
-- @usar: universidad
-- @resultado: 8, 7, 137, 19.5714, 16, 25
SELECT COUNT(*), COUNT(edad), SUM(edad), AVG(edad), MIN(edad), MAX(edad) FROM estudiantes;
