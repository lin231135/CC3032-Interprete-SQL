-- @caso: indice sobre una columna DATE
-- @usar: universidad
-- @resultado: Bruno Díaz | Elena Castro
-- @plan: Índice idx_ingreso
CREATE INDEX idx_ingreso ON estudiantes (ingreso);
SELECT nombre FROM estudiantes WHERE ingreso = '2024-01-10';
