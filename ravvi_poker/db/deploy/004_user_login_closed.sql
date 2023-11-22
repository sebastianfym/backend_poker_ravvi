CREATE INDEX user_login_idx_closed ON public.user_login (user_id, closed_ts);

CREATE OR REPLACE FUNCTION user_login_closed_trg_proc() RETURNS TRIGGER 
AS $$
DECLARE
BEGIN
  UPDATE user_session SET closed_ts = NEW.closed_ts WHERE login_id=NEW.id AND closed_ts IS NULL;
  RETURN NEW;
END; $$
LANGUAGE plpgsql;

CREATE OR REPLACE 
TRIGGER user_login_closed_trg
AFTER UPDATE OF closed_ts ON user_login 
FOR EACH ROW
WHEN (OLD.closed_ts IS NULL AND NEW.closed_ts IS NOT NULL) 
EXECUTE PROCEDURE user_login_closed_trg_proc();
