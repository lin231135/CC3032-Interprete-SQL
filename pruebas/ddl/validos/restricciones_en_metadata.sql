-- @caso: PRIMARY KEY compuesta, UNIQUE, FOREIGN KEY y DEFAULT se guardan en metadata.txt
-- @usar: universidad
-- @contiene: metadata.txt :: PRIMARY KEY (estudiante_id, curso_id)
-- @contiene: metadata.txt :: FOREIGN KEY (curso_id) REFERENCES cursos (id)
-- @contiene: metadata.txt :: UNIQUE (nombre)
-- @contiene: metadata.txt :: COLUMNA carrera VARCHAR(30) NULL DEFAULT 'Sistemas'
SELECT COUNT(*) FROM inscripciones;
