-- @caso: SELECT * expande las columnas en orden
-- @usar: universidad
-- @columnas: id, nombre, creditos
-- @resultado: 2, Bases de Datos, 4 | 3, Estructuras de Datos, 4
SELECT * FROM cursos WHERE creditos = 4;
