-- 4. Índices: compare el "plan" (pestaña MENSAJES) antes y después de crear el índice.
--    El índice queda en la carpeta indices/ de la base de datos.

DROP INDEX IF EXISTS idx_edad;
DROP INDEX IF EXISTS idx_insc_curso;

-- sin índice: recorrido completo de la tabla
SELECT nombre, edad FROM estudiantes WHERE edad >= 20;

CREATE INDEX idx_edad ON estudiantes (edad);

-- con índice: solo se leen los registros que indica idx_edad
SELECT nombre, edad FROM estudiantes WHERE edad >= 20;
SELECT nombre FROM estudiantes WHERE edad BETWEEN 17 AND 19;
SELECT nombre FROM estudiantes WHERE edad IN (16, 25);

-- el índice se mantiene al modificar la tabla
INSERT INTO estudiantes (id, nombre, edad) VALUES (9, 'Iván Torres', 21);
UPDATE estudiantes SET edad = 23 WHERE id = 1;
SELECT nombre, edad FROM estudiantes WHERE edad >= 21;
DELETE FROM estudiantes WHERE id = 9;

-- índice usado en un JOIN
CREATE INDEX idx_insc_curso ON inscripciones (curso_id);
SELECT c.nombre, i.estudiante_id, i.nota
FROM cursos c JOIN inscripciones i ON i.curso_id = c.id
WHERE c.creditos >= 4;

UPDATE estudiantes SET edad = 20 WHERE id = 1;
