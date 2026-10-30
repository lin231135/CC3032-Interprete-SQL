-- @caso: PRIMARY KEY repetida dentro del mismo INSERT
-- @usar: universidad
-- @error: restriccion
INSERT INTO cursos VALUES (10, 'A', 1), (10, 'B', 1);
