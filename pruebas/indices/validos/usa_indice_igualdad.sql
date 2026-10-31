-- @caso: WHERE col = valor usa el indice
-- @usar: universidad
-- @resultado: Diego Ruiz | Fernando Paz
-- @plan: Índice idx_carrera sobre estudiantes.carrera
-- @plan: 2 registro(s) leído(s)
CREATE INDEX idx_carrera ON estudiantes (carrera);
SELECT nombre FROM estudiantes WHERE carrera = 'Civil';
