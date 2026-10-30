-- @caso: IF EXISTS / IF NOT EXISTS no producen error
-- @resultado: 0
DROP TABLE IF EXISTS fantasma;
DROP INDEX IF EXISTS idx_fantasma;
CREATE TABLE IF NOT EXISTS x (a INT);
CREATE TABLE IF NOT EXISTS x (a INT, b INT);
SELECT COUNT(*) FROM x;
