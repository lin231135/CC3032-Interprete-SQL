-- @caso: JOIN sin alias, columnas calificadas con el nombre de la tabla
-- @usar: universidad
-- @resultado: Ana López | Carla Méndez | Fernando Paz
SELECT estudiantes.nombre FROM estudiantes JOIN inscripciones ON estudiantes.id = inscripciones.estudiante_id
WHERE inscripciones.nota >= 90;
