-- @caso: UPDATE ... SET columna_not_null = NULL
-- @usar: universidad
-- @error: valor
UPDATE estudiantes SET nombre = NULL WHERE id = 1;
