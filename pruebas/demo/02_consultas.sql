-- 2. SELECT, WHERE, AND/OR, ORDER BY (ejecute antes 01_esquema_y_datos.sql).
--    Seleccione una sola consulta y presione F5 para ejecutar solo esa.

-- ejemplo del enunciado
SELECT nombre
FROM estudiantes
WHERE edad >= 18;

SELECT nombre, edad, carrera
FROM estudiantes
WHERE (carrera = 'Sistemas' OR carrera = 'Civil') AND activo
ORDER BY edad DESC;

SELECT nombre, ingreso
FROM estudiantes
WHERE ingreso BETWEEN '2023-01-01' AND '2024-12-31'
ORDER BY ingreso, nombre;

SELECT nombre FROM estudiantes WHERE nombre LIKE '%a %' OR edad IS NULL;

SELECT DISTINCT carrera FROM estudiantes ORDER BY carrera;

SELECT nombre, edad * 12 AS meses, 'Carné ' || id AS carne
FROM estudiantes
WHERE id IN (1, 3, 5)
ORDER BY 2 DESC;
