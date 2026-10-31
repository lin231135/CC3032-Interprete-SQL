-- @caso: UPDATE y DELETE usan el indice para encontrar los registros
-- @usar: universidad
-- @resultado: 6
-- @plan: Índice idx_edad sobre estudiantes.edad  [edad = 16] → 1 registro(s) candidato(s)
CREATE INDEX idx_edad ON estudiantes (edad);
UPDATE estudiantes SET edad = 17 WHERE edad = 16;
DELETE FROM estudiantes WHERE edad = 17 AND id = 7;
SELECT COUNT(*) FROM estudiantes WHERE edad >= 17;
