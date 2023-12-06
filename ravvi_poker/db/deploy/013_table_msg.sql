CREATE TABLE public.table_msg (
	id serial4 NOT NULL,
	cmd_id int8 NULL,
	client_id int8 NULL,
	table_id int8 NOT NULL,
	game_id int8 NULL,
	msg_type int4 NOT NULL,
	props jsonb NULL,
	created_ts timestamp NOT NULL DEFAULT now_utc(),
	CONSTRAINT table_msg_pkey PRIMARY KEY (id),
	CONSTRAINT table_msg_fk_cmd FOREIGN KEY (cmd_id) REFERENCES public.table_cmd(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
	CONSTRAINT table_msg_fk_client FOREIGN KEY (client_id) REFERENCES public.user_client(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
	CONSTRAINT table_msg_fk_table FOREIGN KEY (table_id) REFERENCES public.table_profile(id) ON DELETE RESTRICT ON UPDATE RESTRICT,
	CONSTRAINT table_msg_fk_game FOREIGN KEY (game_id) REFERENCES public.poker_game(id) ON DELETE RESTRICT ON UPDATE RESTRICT
);
-- CREATE INDEX table_msg_idx_client ON public.table_msg USING btree (client_id);
-- CREATE INDEX table_msg_idx_table ON public.table_msg USING btree (table_id);

CREATE OR REPLACE FUNCTION table_msg_created_trg_func() RETURNS trigger 
AS $$
DECLARE
  payload VARCHAR;
  x VARCHAR;
BEGIN
  SELECT json_build_object('msg_id', NEW.id, 'table_id',NEW.table_id)::VARCHAR INTO payload;
  SELECT pg_notify('table_msg', payload) INTO x;
  RETURN NEW;
END; $$
LANGUAGE plpgsql;

CREATE OR REPLACE 
TRIGGER table_msg_created_trg
AFTER INSERT ON table_msg
FOR EACH ROW
EXECUTE FUNCTION table_msg_created_trg_func();