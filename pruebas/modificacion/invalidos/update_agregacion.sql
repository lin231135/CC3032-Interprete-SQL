-- @caso: funcion de agregacion en SET
-- @usar: universidad
-- @error: agregacion
UPDATE cursos SET creditos = MAX(creditos);
