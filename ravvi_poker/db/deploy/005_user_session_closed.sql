CREATE INDEX user_session_idx_closed ON public.user_session (login_id, closed_ts);

CREATE OR REPLACE FUNCTION user_session_closed_trg_func() RETURNS TRIGGER 
AS $$
DECLARE
BEGIN
  UPDATE user_client SET closed_ts = NEW.closed_ts WHERE session_id=NEW.id AND closed_ts IS NULL;
  RETURN NEW;
END; $$
LANGUAGE plpgsql;

CREATE OR REPLACE 
TRIGGER user_session_closed_trg
AFTER UPDATE OF closed_ts ON user_session
FOR EACH ROW
WHEN (OLD.closed_ts IS NULL AND NEW.closed_ts IS NOT NULL) 
EXECUTE PROCEDURE user_session_closed_trg_func();
