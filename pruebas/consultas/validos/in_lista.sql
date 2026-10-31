-- @caso: IN con una lista de valores y NOT
-- @usar: universidad
-- @resultado: Bruno Díaz | Diego Ruiz | Fernando Paz
SELECT nombre FROM estudiantes WHERE id IN (2, 4, 6) AND NOT activo = FALSE;
