-- Base de ejemplo del enunciado: estudiantes, cursos e inscripciones.
-- La usan los casos de la bateria con `-- @usar: universidad`.

CREATE TABLE estudiantes (
    id       INT PRIMARY KEY,
    nombre   VARCHAR(50) NOT NULL,
    edad     INT,
    carrera  VARCHAR(30) DEFAULT 'Sistemas',
    activo   BOOLEAN DEFAULT TRUE,
    ingreso  DATE
);

CREATE TABLE cursos (
    id        INT PRIMARY KEY,
    nombre    VARCHAR(40) NOT NULL UNIQUE,
    creditos  INT NOT NULL
);

CREATE TABLE inscripciones (
    estudiante_id  INT NOT NULL REFERENCES estudiantes(id),
    curso_id       INT NOT NULL REFERENCES cursos(id),
    nota           FLOAT,
    PRIMARY KEY (estudiante_id, curso_id)
);

INSERT INTO estudiantes (id, nombre, edad, carrera, activo, ingreso) VALUES
    (1, 'Ana López', 20, 'Sistemas', TRUE, '2023-01-15'),
    (2, 'Bruno Díaz', 17, 'Industrial', TRUE, '2024-01-10'),
    (3, 'Carla Méndez', 22, 'Sistemas', FALSE, '2021-07-01'),
    (4, 'Diego Ruiz', 19, 'Civil', TRUE, '2023-07-03'),
    (5, 'Elena Castro', 18, 'Sistemas', TRUE, '2024-01-10'),
    (6, 'Fernando Paz', 25, 'Civil', TRUE, '2019-01-20'),
    (7, 'Gabriela Soto', 16, 'Industrial', TRUE, NULL),
    (8, 'Hugo Morales', NULL, 'Sistemas', TRUE, '2022-01-12');

INSERT INTO cursos VALUES
    (1, 'Compiladores', 5),
    (2, 'Bases de Datos', 4),
    (3, 'Estructuras de Datos', 4),
    (4, 'Cálculo', 3),
    (5, 'Física', 3);

INSERT INTO inscripciones VALUES
    (1, 1, 85.5), (1, 2, 90), (1, 3, 78),
    (2, 3, 60), (2, 4, 72.5),
    (3, 1, 95), (3, 2, 88),
    (4, 3, 55), (4, 4, NULL),
    (5, 1, 70), (5, 3, 82),
    (6, 4, 91),
    (8, 2, 64);
