-- @caso: ORDER BY con varias claves, DESC y NULL primero
-- @usar: universidad
-- @resultado: Sistemas, Hugo Morales | Sistemas, Elena Castro | Sistemas, Ana López | Sistemas, Carla Méndez | Industrial, Gabriela Soto | Industrial, Bruno Díaz | Civil, Diego Ruiz | Civil, Fernando Paz
SELECT carrera, nombre FROM estudiantes ORDER BY carrera DESC, edad;
