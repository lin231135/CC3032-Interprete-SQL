-- @caso: CREATE INDEX crea el archivo del indice y lo registra en metadata.txt
-- @usar: universidad
-- @existe: indices/idx_edad.idx
-- @contiene: metadata.txt :: INDICE idx_edad ON estudiantes (edad)
-- @contiene: indices/idx_edad.idx :: 18|4
-- @contiene: indices/idx_edad.idx :: 20|0
CREATE INDEX idx_edad ON estudiantes (edad);
