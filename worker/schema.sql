-- NPPU storage. Replaces data/<table>/*.json and pins.json.
--
-- Ratings are per table, so players is keyed by (table, player). A person is
-- one person though, so codes is keyed by the player alone - the same identity
-- across every table, exactly as pins.json worked.
--
-- name_key is the canonical form (casefolded, whitespace collapsed) so "Ola",
-- "ola" and " OLA " are one player; display is the spelling first registered.

CREATE TABLE IF NOT EXISTS codes (
  name_key   TEXT PRIMARY KEY,
  display    TEXT NOT NULL,
  code       TEXT NOT NULL,
  registered TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS players (
  table_name   TEXT    NOT NULL,
  name_key     TEXT    NOT NULL,
  display      TEXT    NOT NULL,
  elo          REAL    NOT NULL DEFAULT 1000,
  k_fac        INTEGER NOT NULL DEFAULT 40,
  games_played INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (table_name, name_key)
);

CREATE TABLE IF NOT EXISTS matches (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  table_name  TEXT    NOT NULL,
  player_a    TEXT    NOT NULL,
  player_b    TEXT    NOT NULL,
  winner      TEXT    NOT NULL,
  games_won_a INTEGER NOT NULL,
  games_won_b INTEGER NOT NULL,
  games       TEXT    NOT NULL,   -- json: [[11,9],[8,11],...]
  played_at   TEXT    NOT NULL,
  elo_change_a REAL,              -- rating each player gained/lost here;
  elo_change_b REAL               -- null on matches recorded before this existed
);

-- the leaderboard and the recent-match list are both just queries now,
-- so there is no stored elo_ranking.json to keep in sync
CREATE INDEX IF NOT EXISTS players_by_elo ON players (table_name, elo DESC);
CREATE INDEX IF NOT EXISTS matches_by_time ON matches (table_name, id DESC);

-- home-page announcements, written from /admin
CREATE TABLE IF NOT EXISTS announcements (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  body      TEXT NOT NULL,
  posted_at TEXT NOT NULL
);
