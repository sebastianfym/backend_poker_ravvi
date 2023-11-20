ALTER TABLE public.poker_event RENAME TO "event";
ALTER TABLE public."event" RENAME COLUMN event_type TO "type";
ALTER TABLE public."event" RENAME COLUMN event_props TO props;
ALTER TABLE public."event" RENAME COLUMN event_ts TO created_ts;
ALTER TABLE public."event" DROP COLUMN user_id;

ALTER TABLE
  "public"."event"
ADD COLUMN
  "client_id" INT8 NULL,
ALTER COLUMN
  "created_ts"
SET DEFAULT
  now_utc ();

ALTER TABLE
  "public"."event"
ADD
  CONSTRAINT "event_fk_client" 
  FOREIGN KEY ("client_id") 
  REFERENCES "public"."user_client" ("id") 
  ON UPDATE NO ACTION ON DELETE NO ACTION;