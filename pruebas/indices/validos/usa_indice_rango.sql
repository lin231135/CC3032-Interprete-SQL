-- @caso: WHERE col >= valor usa el indice (solo se leen 5 de 8 registros)
-- @usar: universidad
-- @resultado: Ana López | Diego Ruiz | Elena Castro | Fernando Paz
-- @plan: Índice idx_edad
-- @plan: 5 registro(s) leído(s)
CREATE INDEX idx_edad ON estudiantes (edad);
SELECT nombre FROM estudiantes WHERE edad >= 18 AND activo;
