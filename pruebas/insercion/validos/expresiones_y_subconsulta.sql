-- @caso: expresiones y subconsulta escalar dentro de VALUES
-- @usar: universidad
-- @resultado: 6, Redes, 8
INSERT INTO cursos VALUES ((SELECT MAX(id) + 1 FROM cursos), 'Re' || 'des', 2 * 4);
SELECT id, nombre, creditos FROM cursos WHERE nombre = 'Redes';
