-- One-off migration for a database created before matches stored elo changes.
-- Run once:  npx wrangler d1 execute nppu --remote --file=worker/add_elo_change.sql
ALTER TABLE matches ADD COLUMN elo_change_a REAL;
ALTER TABLE matches ADD COLUMN elo_change_b REAL;
