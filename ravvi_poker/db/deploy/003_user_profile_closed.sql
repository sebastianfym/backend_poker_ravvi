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
