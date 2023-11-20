CREATE TABLE public.user_client (
	id serial4 NOT NULL,
	session_id int8 NOT NULL,
	created_ts timestamp NOT NULL DEFAULT now_utc(),
	closed_ts timestamp NULL,
	CONSTRAINT user_client_pkey PRIMARY KEY (id),
	CONSTRAINT user_client_fk_session FOREIGN KEY (session_id) REFERENCES public.user_session(id) ON DELETE RESTRICT ON UPDATE RESTRICT
);

CREATE OR REPLACE FUNCTION user_client_notify() RETURNS trigger 
AS $$
DECLARE
  payload VARCHAR;
  x VARCHAR;
BEGIN
  SELECT json_build_object('client_id',NEW.id)::VARCHAR INTO payload;
  --IF OLD.closed_ts IS NULL AND NEW.closed_ts IS NOT NULL THEN
  SELECT pg_notify('user_client_closed', payload) INTO x;
  --END IF;
  RETURN NULL;
END; $$
LANGUAGE plpgsql;

CREATE OR REPLACE 
TRIGGER user_client_trigger
AFTER UPDATE OF closed_ts ON "user_client" 
FOR EACH ROW
EXECUTE FUNCTION user_client_notify();
