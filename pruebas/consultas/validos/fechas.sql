-- @caso: comparacion de DATE con un texto 'YYYY-MM-DD'
-- @usar: universidad
-- @resultado: Ana López, 2023-01-15 | Diego Ruiz, 2023-07-03
SELECT nombre, ingreso FROM estudiantes WHERE ingreso BETWEEN '2023-01-01' AND DATE '2023-12-31';
