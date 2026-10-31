-- @caso: DELETE quita la entrada y reajusta las posiciones del indice
-- @resultado: 5
-- @contiene: indices/idx_v.idx :: 50|3
-- @contiene: indices/idx_v.idx :: 60|4
CREATE TABLE p (id INT PRIMARY KEY, v INT);
INSERT INTO p VALUES (1, 10), (2, 20), (3, 30), (4, 40), (5, 50), (6, 60);
CREATE INDEX idx_v ON p (v);
DELETE FROM p WHERE id = 2;
SELECT id FROM p WHERE v = 50;
