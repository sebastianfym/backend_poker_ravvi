ALTER TABLE
  "poker_game"
ADD COLUMN
  "game_type" varchar(64) NOT NULL,
ADD COLUMN
  "game_subtype" VARCHAR(64) NOT NULL;

CREATE INDEX
  "poker_game_type" on "poker_game" ("game_type" ASC, "game_subtype" ASC);