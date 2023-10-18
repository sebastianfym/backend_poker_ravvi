ALTER TABLE
  "public"."poker_table"
ADD COLUMN
  "n_bots" SMALLINT NOT NULL DEFAULT 0;

UPDATE "public"."poker_table" SET n_bots=3 WHERE id<1000;