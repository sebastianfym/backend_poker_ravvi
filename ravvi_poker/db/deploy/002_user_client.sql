CREATE TABLE public.user_client (
	id serial4 NOT NULL,
	session_id int8 NOT NULL,
	created_ts timestamp NOT NULL DEFAULT now_utc(),
	closed_ts timestamp NULL,
	CONSTRAINT user_client_pkey PRIMARY KEY (id),
	CONSTRAINT user_client_fk_session FOREIGN KEY (session_id) REFERENCES public.user_session(id) ON DELETE RESTRICT ON UPDATE RESTRICT
);

CREATE INDEX user_client_idx_closed ON public.user_client (session_id, closed_ts);

CREATE OR REPLACE FUNCTION user_client_closed_trg_proc() RETURNS TRIGGER 
AS $$
DECLARE
  payload VARCHAR;
  x VARCHAR;
BEGIN
  SELECT json_build_object('client_id',NEW.id)::VARCHAR INTO payload;
  SELECT pg_notify('user_client_closed', payload) INTO x;
  RETURN NEW;
END; $$
LANGUAGE plpgsql;

CREATE OR REPLACE 
TRIGGER user_client_closed_trg
AFTER UPDATE OF closed_ts ON user_client 
FOR EACH ROW
WHEN (OLD.closed_ts IS NULL AND NEW.closed_ts IS NOT NULL)
EXECUTE PROCEDURE user_client_closed_trg_proc();
