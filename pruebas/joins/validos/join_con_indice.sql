-- @caso: el JOIN usa el indice de la tabla interna
-- @usar: universidad
-- @resultado: Cálculo, NULL | Cálculo, 72.5 | Cálculo, 91.0
-- @plan: Índice idx_insc_curso en JOIN
CREATE INDEX idx_insc_curso ON inscripciones (curso_id);
SELECT c.nombre, i.nota FROM cursos c JOIN inscripciones i ON i.curso_id = c.id WHERE c.id = 4 ORDER BY i.nota;
