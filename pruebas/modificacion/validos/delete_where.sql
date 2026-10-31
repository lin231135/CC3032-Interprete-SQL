-- @caso: DELETE con OR e IS NULL
-- @usar: universidad
-- @resultado: 9
DELETE FROM inscripciones WHERE nota < 65 OR nota IS NULL;
SELECT COUNT(*) FROM inscripciones;
