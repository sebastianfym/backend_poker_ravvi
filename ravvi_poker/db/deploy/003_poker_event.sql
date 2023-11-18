ALTER TABLE
  "public"."poker_event"
ADD COLUMN
  "client_id" INT8 NULL,
ALTER COLUMN
  "event_ts"
SET DEFAULT
  now_utc ();

ALTER TABLE
  "public"."poker_event"
ADD
  CONSTRAINT "poker_event_client_id" 
  FOREIGN KEY ("client_id") 
  REFERENCES "public"."user_client" ("id") 
  ON UPDATE NO ACTION ON DELETE NO ACTION;