-- @caso: una FOREIGN KEY NULL no se verifica
-- @resultado: 1
CREATE TABLE padre (id INT PRIMARY KEY);
CREATE TABLE hijo (p INT REFERENCES padre(id));
INSERT INTO hijo VALUES (NULL);
SELECT COUNT(*) FROM hijo;
