ALTER TABLE public.poker_table RENAME TO table_profile;
ALTER TABLE public.table_profile RENAME COLUMN game_settings TO props;
ALTER TABLE public.table_profile ALTER COLUMN created_ts SET DEFAULT now_utc();
ALTER TABLE public.table_profile ADD engine_id bigint DEFAULT NULL;
ALTER TABLE public.table_profile ADD engine_status smallint NOT NULL DEFAULT 0;

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

CREATE OR REPLACE FUNCTION table_profile_status_trg_func() RETURNS TRIGGER 
AS $$
DECLARE
  payload VARCHAR;
  x VARCHAR;
BEGIN
  SELECT json_build_object('table_id',NEW.id,'engine_status',NEW.engine_status,'engine_id',NEW.engine_id)::VARCHAR INTO payload;
  SELECT pg_notify('table_profile_status', payload) INTO x;
  RETURN NEW;
END; $$
LANGUAGE plpgsql;

CREATE OR REPLACE 
TRIGGER table_profile_status_trg
AFTER UPDATE ON table_profile
FOR EACH ROW
WHEN (OLD.engine_status!=NEW.engine_status OR OLD.engine_id!=NEW.engine_id) 
EXECUTE PROCEDURE table_profile_status_trg_func();
