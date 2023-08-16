ALTER TABLE
  "public"."poker_table"
ALTER COLUMN "table_type" SET NOT NULL,
ALTER COLUMN "table_type"  DROP DEFAULT,
ALTER COLUMN "game_type" SET NOT NULL, 
ALTER COLUMN "game_type"  DROP DEFAULT,
ALTER COLUMN "game_subtype" SET NOT NULL,
ALTER COLUMN "game_subtype" DROP DEFAULT;

ALTER TABLE
  "public"."poker_table"
ADD COLUMN
  "parent_id" bigint NULL DEFAULT NULL;

ALTER TABLE
  "public"."poker_table"
ADD
  CONSTRAINT "poker_table_parent" FOREIGN KEY ("parent_id") REFERENCES "public"."poker_table" ("id") ON UPDATE CASCADE ON DELETE CASCADE