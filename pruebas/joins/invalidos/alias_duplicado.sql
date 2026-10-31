-- @caso: el mismo alias dos veces
-- @usar: universidad
-- @error: referencia
SELECT x.nombre FROM estudiantes x JOIN cursos x ON x.id = x.id;
