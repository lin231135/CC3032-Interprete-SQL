-- @caso: ON compara VARCHAR con INT
-- @usar: universidad
-- @error: tipo
SELECT * FROM estudiantes e JOIN cursos c ON e.nombre = c.id;
