-- @caso: col IN (subconsulta) usa el indice de col
-- @usar: universidad
-- @resultado: Ana López | Carla Méndez | Elena Castro
-- @plan: Índice idx_id sobre estudiantes.id
CREATE INDEX idx_id ON estudiantes (id);
SELECT nombre FROM estudiantes WHERE id IN (SELECT estudiante_id FROM inscripciones WHERE curso_id = 1);
