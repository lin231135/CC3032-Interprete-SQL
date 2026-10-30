-- @caso: UPDATE que repite la PRIMARY KEY
-- @usar: universidad
-- @error: restriccion
UPDATE cursos SET id = 2 WHERE id = 5;
