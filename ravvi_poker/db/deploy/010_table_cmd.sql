CREATE TABLE public.table_cmd (
	id serial4 NOT NULL,
	client_id int8 NOT NULL,
	table_id int8 NOT NULL,
	cmd_type int4 NOT NULL,
	props jsonb NULL,
	created_ts timestamp NOT NULL DEFAULT now_utc(),
	processed_ts timestamp NULL,
	CONSTRAINT table_cmd_pkey PRIMARY KEY (id),
	CONSTRAINT table_cmd_fk_client FOREIGN KEY (client_id) REFERENCES public.user_client(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
	CONSTRAINT table_cmd_fk_table FOREIGN KEY (table_id) REFERENCES public.table_profile(id) ON DELETE CASCADE ON UPDATE RESTRICT
);
-- CREATE INDEX table_cmd_idx_client ON public.table_cmd USING btree (client_id);
-- CREATE INDEX table_cmd_idx_table ON public.table_cmd USING btree (table_id);

CREATE OR REPLACE FUNCTION table_cmd_notify() RETURNS trigger 
AS $$
DECLARE
  payload VARCHAR;
  x VARCHAR;
BEGIN
  SELECT json_build_object('table_id',NEW.table_id,'cmd_id', NEW.id)::VARCHAR INTO payload;
  SELECT pg_notify('table_cmd', payload) INTO x;
  RETURN NULL;
END; $$
LANGUAGE plpgsql;

CREATE OR REPLACE 
TRIGGER table_cmd_trigger
AFTER INSERT ON table_cmd
FOR EACH ROW
EXECUTE FUNCTION table_cmd_notify();