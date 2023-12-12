ALTER TABLE public.user_profile ADD balance numeric(20,0) NOT NULL DEFAULT 1000;
ALTER TABLE public.user_profile RENAME COLUMN username TO name;

CREATE OR REPLACE FUNCTION user_profile_name_trg_proc() RETURNS TRIGGER 
AS $$
BEGIN
  IF NEW.name IS NULL OR LENGTH(NEW.name)=0 THEN
    select CONCAT('u',NEW.id) into new.name;
  END IF;
  RETURN NEW;
END; $$
LANGUAGE plpgsql;

CREATE OR REPLACE 
TRIGGER user_profile_name_trg
BEFORE INSERT OR UPDATE OF name ON user_profile
FOR EACH ROW
WHEN (NEW.name IS NULL OR LENGTH(NEW.name)=0)
EXECUTE PROCEDURE user_profile_name_trg_proc();

CREATE OR REPLACE FUNCTION user_profile_closed_trg_proc() RETURNS TRIGGER 
AS $$
DECLARE
BEGIN
  UPDATE user_login SET closed_ts = NEW.closed_ts WHERE user_id=OLD.id AND closed_ts IS NULL;
  RETURN NEW;
END; $$
LANGUAGE plpgsql;

CREATE OR REPLACE 
TRIGGER user_profile_closed_trg
AFTER UPDATE OF closed_ts ON user_profile 
FOR EACH ROW
WHEN (OLD.closed_ts IS NULL AND NEW.closed_ts IS NOT NULL)
EXECUTE PROCEDURE user_profile_closed_trg_proc();
