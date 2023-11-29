ALTER TABLE public.poker_table RENAME TO table_profile;
ALTER TABLE public.table_profile RENAME COLUMN game_settings TO props;
ALTER TABLE public.table_profile ALTER COLUMN created_ts SET DEFAULT now_utc();

CREATE OR REPLACE FUNCTION table_profile_created_trg_func() RETURNS TRIGGER 
AS $$
DECLARE
  payload VARCHAR;
  x VARCHAR;
BEGIN
  SELECT json_build_object('table_id',NEW.id)::VARCHAR INTO payload;
  SELECT pg_notify('table_profile_created', payload) INTO x;
  RETURN NEW;
END; $$
LANGUAGE plpgsql;

CREATE OR REPLACE 
TRIGGER table_profile_created_trg
AFTER INSERT ON table_profile
FOR EACH ROW
EXECUTE PROCEDURE table_profile_created_trg_func();
