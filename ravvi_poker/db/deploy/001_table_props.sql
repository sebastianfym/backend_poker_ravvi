ALTER TABLE
  "public"."poker_table"
ALTER COLUMN "table_type" SET NOT NULL,
ALTER COLUMN "table_type"  DROP DEFAULT,
ALTER COLUMN "game_type" SET NOT NULL, 
ALTER COLUMN "game_type"  DROP DEFAULT,
ALTER COLUMN "game_subtype" SET NOT NULL,
ALTER COLUMN "game_subtype" DROP DEFAULT;