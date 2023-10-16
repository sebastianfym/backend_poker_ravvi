ALTER TABLE
  "public"."poker_table_user"
DROP COLUMN
  "exit_ts"
;

ALTER TABLE
  "public"."poker_table_user"
RENAME COLUMN
  "exit_game_id" TO "last_game_id"
;