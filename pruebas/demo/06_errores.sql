-- 6. Errores semánticos: el análisis los reporta TODOS (pestaña PROBLEMAS) y no
--    se ejecuta ninguna sentencia. Doble clic en un error para ir a la línea.
--    (Pruebe también F6, que solo analiza.)

SELECT nombre FROM alumnos;                                   -- tabla inexistente
SELECT apellido FROM estudiantes;                             -- columna inexistente
SELECT nombre FROM estudiantes WHERE edad = 'veinte';         -- tipos incompatibles
INSERT INTO cursos VALUES (6, 'Redes');                       -- cantidad de valores
INSERT INTO cursos VALUES (7, NULL, 3);                       -- NULL en NOT NULL
INSERT INTO estudiantes (id, nombre, ingreso) VALUES (9, 'X', '2024-02-30');  -- fecha inválida
SELECT nombre FROM estudiantes e JOIN cursos c ON c.id = e.id;   -- columna ambigua
DROP INDEX idx_que_no_existe;                                 -- índice inexistente
CREATE INDEX idx_edad ON estudiantes (edad);                  -- índice duplicado
SELECT nombre FROM estudiantes WHERE edad = (SELECT id, creditos FROM cursos);  -- subconsulta escalar
SELECT carrera, nombre, COUNT(*) FROM estudiantes GROUP BY carrera;            -- GROUP BY
