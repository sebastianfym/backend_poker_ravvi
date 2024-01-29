
CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;

CREATE TYPE public.user_role_enum AS ENUM (
    'P',
    'O',
    'M',
    'A',
    'S'
);

CREATE FUNCTION public.club_name_trg_proc() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  IF NEW.name IS NULL OR LENGTH(NEW.name)=0 THEN
    select CONCAT('CLUB-',NEW.id) into new.name;
  END IF;
  RETURN NEW;
END; $$;

CREATE FUNCTION public.now_utc() RETURNS timestamp without time zone
    LANGUAGE sql
    AS $$
  select now() at time zone 'utc';
$$;

CREATE FUNCTION public.table_cmd_created_trg_func() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
  payload VARCHAR;
  x VARCHAR;
BEGIN
  SELECT json_build_object('cmd_id', NEW.id, 'table_id',NEW.table_id)::VARCHAR INTO payload;
  SELECT pg_notify('table_cmd', payload) INTO x;
  RETURN NEW;
END; $$;

CREATE FUNCTION public.table_msg_created_trg_func() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
  payload VARCHAR;
  x VARCHAR;
BEGIN
  SELECT json_build_object('msg_id', NEW.id, 'table_id',NEW.table_id)::VARCHAR INTO payload;
  SELECT pg_notify('table_msg', payload) INTO x;
  RETURN NEW;
END; $$;

CREATE FUNCTION public.table_profile_created_trg_func() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
  payload VARCHAR;
  x VARCHAR;
BEGIN
  SELECT json_build_object('table_id',NEW.id)::VARCHAR INTO payload;
  SELECT pg_notify('table_profile_created', payload) INTO x;
  RETURN NEW;
END; $$;

CREATE FUNCTION public.table_profile_status_trg_func() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
  payload VARCHAR;
  x VARCHAR;
BEGIN
  SELECT json_build_object('table_id',NEW.id,'engine_status',NEW.engine_status,'engine_id',NEW.engine_id)::VARCHAR INTO payload;
  SELECT pg_notify('table_profile_status', payload) INTO x;
  RETURN NEW;
END; $$;

CREATE FUNCTION public.user_client_closed_trg_proc() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
  payload VARCHAR;
  x VARCHAR;
BEGIN
  SELECT json_build_object('client_id',NEW.id)::VARCHAR INTO payload;
  SELECT pg_notify('user_client_closed', payload) INTO x;
  RETURN NEW;
END; $$;

CREATE FUNCTION public.user_login_closed_trg_proc() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
BEGIN
  UPDATE user_session SET closed_ts = NEW.closed_ts WHERE login_id=NEW.id AND closed_ts IS NULL;
  RETURN NEW;
END; $$;

CREATE FUNCTION public.user_profile_closed_trg_proc() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
BEGIN
  UPDATE user_login SET closed_ts = NEW.closed_ts WHERE user_id=OLD.id AND closed_ts IS NULL;
  RETURN NEW;
END; $$;

CREATE FUNCTION public.user_profile_name_trg_proc() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
  IF NEW.name IS NULL OR LENGTH(NEW.name)=0 THEN
    select CONCAT('u',NEW.id) into new.name;
  END IF;
  RETURN NEW;
END; $$;

CREATE FUNCTION public.user_session_closed_trg_func() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
BEGIN
  UPDATE user_client SET closed_ts = NEW.closed_ts WHERE session_id=NEW.id AND closed_ts IS NULL;
  RETURN NEW;
END; $$;

CREATE TABLE public.club_profile (
    id bigint NOT NULL,
    name character varying(200) DEFAULT NULL::character varying,
    description character varying(1000) DEFAULT NULL::character varying,
    image_id bigint,
    service_balance numeric(18,2) DEFAULT 0 NOT NULL,
    service_limit numeric(18,2) DEFAULT 0 NOT NULL,
    created_ts timestamp without time zone DEFAULT public.now_utc() NOT NULL,
    closed_ts timestamp without time zone
);

CREATE SEQUENCE public.club_profile_id_seq
    START WITH 1000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.club_profile_id_seq OWNED BY public.club_profile.id;

CREATE TABLE public.game_player (
    game_id bigint NOT NULL,
    user_id bigint NOT NULL,
    balance_begin numeric(16,2),
    balance_end numeric(16,2)
);

CREATE TABLE public.game_profile (
    id bigint NOT NULL,
    table_id bigint NOT NULL,
    begin_ts timestamp without time zone DEFAULT public.now_utc() NOT NULL,
    end_ts timestamp without time zone,
    game_type character varying(64) NOT NULL,
    game_subtype character varying(64) NOT NULL,
    props jsonb
);

CREATE SEQUENCE public.game_profile_id_seq
    START WITH 1000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.game_profile_id_seq OWNED BY public.game_profile.id;

CREATE TABLE public.image (
    id bigint NOT NULL,
    owner_id bigint,
    created_ts timestamp without time zone DEFAULT public.now_utc() NOT NULL,
    image_data text,
    mime_type character varying(100) DEFAULT NULL::character varying
);

CREATE SEQUENCE public.image_id_seq
    START WITH 1000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.image_id_seq OWNED BY public.image.id;

CREATE TABLE public.table_cmd (
    id bigint NOT NULL,
    client_id bigint NOT NULL,
    table_id bigint NOT NULL,
    cmd_type integer NOT NULL,
    props jsonb,
    created_ts timestamp without time zone DEFAULT public.now_utc() NOT NULL,
    processed_ts timestamp without time zone
);

CREATE SEQUENCE public.table_cmd_id_seq
    START WITH 1000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.table_cmd_id_seq OWNED BY public.table_cmd.id;

CREATE TABLE public.table_msg (
    id bigint NOT NULL,
    cmd_id bigint,
    client_id bigint,
    table_id bigint NOT NULL,
    game_id bigint,
    msg_type integer NOT NULL,
    props jsonb,
    created_ts timestamp without time zone DEFAULT public.now_utc() NOT NULL
);

CREATE SEQUENCE public.table_msg_id_seq
    START WITH 1000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.table_msg_id_seq OWNED BY public.table_msg.id;

CREATE TABLE public.table_profile (
    id bigint NOT NULL,
    parent_id bigint,
    club_id bigint DEFAULT 0 NOT NULL,
    table_type character varying(100) NOT NULL,
    game_type character varying(100) NOT NULL,
    table_name character varying(100) DEFAULT NULL::character varying,
    game_subtype character varying(100) NOT NULL,
    table_seats smallint,
    props jsonb,
    created_ts timestamp without time zone DEFAULT public.now_utc() NOT NULL,
    opened_ts timestamp without time zone,
    closed_ts timestamp without time zone,
    n_bots smallint DEFAULT 0 NOT NULL,
    engine_id bigint,
    engine_status smallint DEFAULT 0 NOT NULL
);

CREATE SEQUENCE public.table_profile_id_seq
    START WITH 1000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.table_profile_id_seq OWNED BY public.table_profile.id;

CREATE TABLE public.table_session (
    id integer NOT NULL,
    table_id bigint NOT NULL,
    account_id bigint NOT NULL,
    created_ts timestamp without time zone DEFAULT public.now_utc() NOT NULL,
    opened_ts timestamp without time zone,
    closed_ts timestamp without time zone
);

CREATE SEQUENCE public.table_session_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.table_session_id_seq OWNED BY public.table_session.id;

CREATE TABLE public.temp_email (
    id bigint NOT NULL,
    uuid uuid DEFAULT public.uuid_generate_v4(),
    user_id bigint NOT NULL,
    temp_email character varying(100) NOT NULL,
    created_ts timestamp without time zone DEFAULT public.now_utc(),
    closed_ts timestamp without time zone
);

CREATE SEQUENCE public.temp_email_id_seq
    START WITH 1000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.temp_email_id_seq OWNED BY public.temp_email.id;

CREATE TABLE public.user_account (
    id bigint NOT NULL,
    club_id bigint DEFAULT 0 NOT NULL,
    user_id bigint NOT NULL,
    user_role public.user_role_enum DEFAULT 'P'::public.user_role_enum NOT NULL,
    created_ts timestamp without time zone DEFAULT public.now_utc() NOT NULL,
    user_comment character varying(255) DEFAULT NULL::character varying,
    approved_ts timestamp without time zone,
    approved_by bigint,
    club_comment character varying(255) DEFAULT NULL::character varying,
    balance numeric(20,4) DEFAULT 0 NOT NULL,
    balance_shared numeric(20,4) DEFAULT 0 NOT NULL,
    closed_ts timestamp without time zone,
    closed_by bigint
);

CREATE SEQUENCE public.user_account_id_seq
    START WITH 1000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.user_account_id_seq OWNED BY public.user_account.id;

CREATE TABLE public.user_account_txn (
    id bigint NOT NULL,
    created_ts timestamp without time zone DEFAULT public.now_utc() NOT NULL,
    account_id bigint NOT NULL,
    txn_type character varying(30) NOT NULL,
    txn_value numeric(20,4) NOT NULL,
    props jsonb
);

CREATE SEQUENCE public.user_account_txn_id_seq
    START WITH 1000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.user_account_txn_id_seq OWNED BY public.user_account_txn.id;

CREATE TABLE public.user_client (
    id bigint NOT NULL,
    session_id bigint NOT NULL,
    created_ts timestamp without time zone DEFAULT public.now_utc() NOT NULL,
    closed_ts timestamp without time zone
);

CREATE SEQUENCE public.user_client_id_seq
    START WITH 1000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.user_client_id_seq OWNED BY public.user_client.id;

CREATE TABLE public.user_device (
    id bigint NOT NULL,
    uuid uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    props jsonb,
    created_ts timestamp without time zone DEFAULT public.now_utc() NOT NULL,
    closed_ts timestamp without time zone
);

CREATE SEQUENCE public.user_device_id_seq
    START WITH 1000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.user_device_id_seq OWNED BY public.user_device.id;

CREATE TABLE public.user_login (
    id bigint NOT NULL,
    uuid uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    user_id bigint NOT NULL,
    device_id bigint NOT NULL,
    created_ts timestamp without time zone DEFAULT public.now_utc() NOT NULL,
    closed_ts timestamp without time zone
);

CREATE SEQUENCE public.user_login_id_seq
    START WITH 1000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.user_login_id_seq OWNED BY public.user_login.id;

CREATE TABLE public.user_profile (
    id bigint NOT NULL,
    uuid uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    name character varying(100) DEFAULT NULL::character varying,
    password_hash character varying(100) DEFAULT NULL::character varying,
    created_ts timestamp without time zone DEFAULT public.now_utc() NOT NULL,
    closed_ts timestamp without time zone,
    email character varying(100) DEFAULT NULL::character varying,
    image_id bigint
);

CREATE SEQUENCE public.user_profile_id_seq
    START WITH 1000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.user_profile_id_seq OWNED BY public.user_profile.id;

CREATE TABLE public.user_session (
    id bigint NOT NULL,
    uuid uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    login_id bigint NOT NULL,
    created_ts timestamp without time zone DEFAULT public.now_utc() NOT NULL,
    used_ts timestamp without time zone,
    closed_ts timestamp without time zone
);

CREATE SEQUENCE public.user_session_id_seq
    START WITH 1000
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE public.user_session_id_seq OWNED BY public.user_session.id;

ALTER TABLE ONLY public.club_profile ALTER COLUMN id SET DEFAULT nextval('public.club_profile_id_seq'::regclass);

ALTER TABLE ONLY public.game_profile ALTER COLUMN id SET DEFAULT nextval('public.game_profile_id_seq'::regclass);

ALTER TABLE ONLY public.image ALTER COLUMN id SET DEFAULT nextval('public.image_id_seq'::regclass);

ALTER TABLE ONLY public.table_cmd ALTER COLUMN id SET DEFAULT nextval('public.table_cmd_id_seq'::regclass);

ALTER TABLE ONLY public.table_msg ALTER COLUMN id SET DEFAULT nextval('public.table_msg_id_seq'::regclass);

ALTER TABLE ONLY public.table_profile ALTER COLUMN id SET DEFAULT nextval('public.table_profile_id_seq'::regclass);

ALTER TABLE ONLY public.table_session ALTER COLUMN id SET DEFAULT nextval('public.table_session_id_seq'::regclass);

ALTER TABLE ONLY public.temp_email ALTER COLUMN id SET DEFAULT nextval('public.temp_email_id_seq'::regclass);

ALTER TABLE ONLY public.user_account ALTER COLUMN id SET DEFAULT nextval('public.user_account_id_seq'::regclass);

ALTER TABLE ONLY public.user_account_txn ALTER COLUMN id SET DEFAULT nextval('public.user_account_txn_id_seq'::regclass);

ALTER TABLE ONLY public.user_client ALTER COLUMN id SET DEFAULT nextval('public.user_client_id_seq'::regclass);

ALTER TABLE ONLY public.user_device ALTER COLUMN id SET DEFAULT nextval('public.user_device_id_seq'::regclass);

ALTER TABLE ONLY public.user_login ALTER COLUMN id SET DEFAULT nextval('public.user_login_id_seq'::regclass);

ALTER TABLE ONLY public.user_profile ALTER COLUMN id SET DEFAULT nextval('public.user_profile_id_seq'::regclass);

ALTER TABLE ONLY public.user_session ALTER COLUMN id SET DEFAULT nextval('public.user_session_id_seq'::regclass);

ALTER TABLE ONLY public.club_profile
    ADD CONSTRAINT club_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.game_player
    ADD CONSTRAINT game_player_pkey PRIMARY KEY (game_id, user_id);

ALTER TABLE ONLY public.game_profile
    ADD CONSTRAINT game_profile_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.image
    ADD CONSTRAINT image_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.table_cmd
    ADD CONSTRAINT table_cmd_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.table_msg
    ADD CONSTRAINT table_msg_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.table_profile
    ADD CONSTRAINT table_profile_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.table_session
    ADD CONSTRAINT table_session_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.temp_email
    ADD CONSTRAINT temp_email_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.temp_email
    ADD CONSTRAINT temp_email_unq_uuid UNIQUE (uuid);

ALTER TABLE ONLY public.user_account
    ADD CONSTRAINT user_account_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.user_account_txn
    ADD CONSTRAINT user_account_txn_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.user_client
    ADD CONSTRAINT user_client_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.user_device
    ADD CONSTRAINT user_device_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.user_device
    ADD CONSTRAINT user_device_uuid_key UNIQUE (uuid);

ALTER TABLE ONLY public.user_login
    ADD CONSTRAINT user_login_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.user_login
    ADD CONSTRAINT user_login_uuid_key UNIQUE (uuid);

ALTER TABLE ONLY public.user_profile
    ADD CONSTRAINT user_profile_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.user_profile
    ADD CONSTRAINT user_profile_uuid_key UNIQUE (uuid);

ALTER TABLE ONLY public.user_session
    ADD CONSTRAINT user_session_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.user_session
    ADD CONSTRAINT user_session_uuid_key UNIQUE (uuid);

CREATE INDEX game_profile_idx_type ON public.game_profile USING btree (game_type, game_subtype);

CREATE INDEX game_profile_idx_user ON public.game_player USING btree (user_id);

CREATE INDEX user_account_idx_user ON public.user_account USING btree (user_id);

CREATE UNIQUE INDEX user_account_unq_clubuser ON public.user_account USING btree (club_id, user_id);

CREATE INDEX user_client_idx_closed ON public.user_client USING btree (session_id, closed_ts);

CREATE INDEX user_login_idx_closed ON public.user_login USING btree (user_id, closed_ts);

CREATE INDEX user_session_idx_closed ON public.user_session USING btree (login_id, closed_ts);

CREATE TRIGGER club_name_trg BEFORE INSERT OR UPDATE ON public.club_profile FOR EACH ROW EXECUTE FUNCTION public.club_name_trg_proc();

CREATE TRIGGER table_cmd_created_trg AFTER INSERT ON public.table_cmd FOR EACH ROW EXECUTE FUNCTION public.table_cmd_created_trg_func();

CREATE TRIGGER table_msg_created_trg AFTER INSERT ON public.table_msg FOR EACH ROW EXECUTE FUNCTION public.table_msg_created_trg_func();

CREATE TRIGGER table_profile_created_trg AFTER INSERT ON public.table_profile FOR EACH ROW EXECUTE FUNCTION public.table_profile_created_trg_func();

CREATE TRIGGER table_profile_status_trg AFTER UPDATE ON public.table_profile FOR EACH ROW WHEN (((old.engine_status <> new.engine_status) OR (old.engine_id <> new.engine_id))) EXECUTE FUNCTION public.table_profile_status_trg_func();

CREATE TRIGGER user_client_closed_trg AFTER UPDATE OF closed_ts ON public.user_client FOR EACH ROW WHEN (((old.closed_ts IS NULL) AND (new.closed_ts IS NOT NULL))) EXECUTE FUNCTION public.user_client_closed_trg_proc();

CREATE TRIGGER user_login_closed_trg AFTER UPDATE OF closed_ts ON public.user_login FOR EACH ROW WHEN (((old.closed_ts IS NULL) AND (new.closed_ts IS NOT NULL))) EXECUTE FUNCTION public.user_login_closed_trg_proc();

CREATE TRIGGER user_profile_closed_trg AFTER UPDATE OF closed_ts ON public.user_profile FOR EACH ROW WHEN (((old.closed_ts IS NULL) AND (new.closed_ts IS NOT NULL))) EXECUTE FUNCTION public.user_profile_closed_trg_proc();

CREATE TRIGGER user_profile_name_trg BEFORE INSERT OR UPDATE OF name ON public.user_profile FOR EACH ROW WHEN (((new.name IS NULL) OR (length((new.name)::text) = 0))) EXECUTE FUNCTION public.user_profile_name_trg_proc();

CREATE TRIGGER user_session_closed_trg AFTER UPDATE OF closed_ts ON public.user_session FOR EACH ROW WHEN (((old.closed_ts IS NULL) AND (new.closed_ts IS NOT NULL))) EXECUTE FUNCTION public.user_session_closed_trg_func();

ALTER TABLE ONLY public.club_profile
    ADD CONSTRAINT club_profile_fk_image FOREIGN KEY (image_id) REFERENCES public.image(id);

ALTER TABLE ONLY public.game_player
    ADD CONSTRAINT game_player_fk_game FOREIGN KEY (game_id) REFERENCES public.game_profile(id);

ALTER TABLE ONLY public.game_player
    ADD CONSTRAINT game_player_fk_user FOREIGN KEY (user_id) REFERENCES public.user_profile(id);

ALTER TABLE ONLY public.game_profile
    ADD CONSTRAINT game_profile_fk_table FOREIGN KEY (table_id) REFERENCES public.table_profile(id);

ALTER TABLE ONLY public.image
    ADD CONSTRAINT image_fk_owner FOREIGN KEY (owner_id) REFERENCES public.user_profile(id);

ALTER TABLE ONLY public.table_cmd
    ADD CONSTRAINT table_cmd_fk_client FOREIGN KEY (client_id) REFERENCES public.user_client(id) ON UPDATE RESTRICT ON DELETE RESTRICT;

ALTER TABLE ONLY public.table_cmd
    ADD CONSTRAINT table_cmd_fk_table FOREIGN KEY (table_id) REFERENCES public.table_profile(id) ON UPDATE RESTRICT ON DELETE CASCADE;

ALTER TABLE ONLY public.table_msg
    ADD CONSTRAINT table_msg_fk_client FOREIGN KEY (client_id) REFERENCES public.user_client(id) ON UPDATE RESTRICT ON DELETE RESTRICT;

ALTER TABLE ONLY public.table_msg
    ADD CONSTRAINT table_msg_fk_cmd FOREIGN KEY (cmd_id) REFERENCES public.table_cmd(id) ON UPDATE RESTRICT ON DELETE RESTRICT;

ALTER TABLE ONLY public.table_msg
    ADD CONSTRAINT table_msg_fk_game FOREIGN KEY (game_id) REFERENCES public.game_profile(id) ON UPDATE RESTRICT ON DELETE RESTRICT;

ALTER TABLE ONLY public.table_msg
    ADD CONSTRAINT table_msg_fk_table FOREIGN KEY (table_id) REFERENCES public.table_profile(id) ON UPDATE RESTRICT ON DELETE RESTRICT;

ALTER TABLE ONLY public.table_profile
    ADD CONSTRAINT table_profile_fk_parent FOREIGN KEY (parent_id) REFERENCES public.table_profile(id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY public.table_session
    ADD CONSTRAINT table_session_fk_account FOREIGN KEY (account_id) REFERENCES public.user_account(id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY public.table_session
    ADD CONSTRAINT table_session_fk_table FOREIGN KEY (table_id) REFERENCES public.table_profile(id) ON UPDATE CASCADE ON DELETE CASCADE;

ALTER TABLE ONLY public.temp_email
    ADD CONSTRAINT temp_email_fk_user FOREIGN KEY (user_id) REFERENCES public.user_profile(id);

ALTER TABLE ONLY public.user_account
    ADD CONSTRAINT user_account_fk_approved_by FOREIGN KEY (approved_by) REFERENCES public.user_profile(id);

ALTER TABLE ONLY public.user_account
    ADD CONSTRAINT user_account_fk_club FOREIGN KEY (club_id) REFERENCES public.club_profile(id);

ALTER TABLE ONLY public.user_account
    ADD CONSTRAINT user_account_fk_user FOREIGN KEY (user_id) REFERENCES public.user_profile(id);

ALTER TABLE ONLY public.user_account_txn
    ADD CONSTRAINT user_account_txn_fk_account FOREIGN KEY (account_id) REFERENCES public.user_account(id);

ALTER TABLE ONLY public.user_client
    ADD CONSTRAINT user_client_fk_session FOREIGN KEY (session_id) REFERENCES public.user_session(id) ON UPDATE RESTRICT ON DELETE RESTRICT;

ALTER TABLE ONLY public.user_login
    ADD CONSTRAINT user_login_fk_device FOREIGN KEY (device_id) REFERENCES public.user_device(id);

ALTER TABLE ONLY public.user_login
    ADD CONSTRAINT user_login_fk_user FOREIGN KEY (user_id) REFERENCES public.user_profile(id);

ALTER TABLE ONLY public.user_profile
    ADD CONSTRAINT user_profile_fk_image FOREIGN KEY (image_id) REFERENCES public.image(id);

ALTER TABLE ONLY public.user_session
    ADD CONSTRAINT user_session_fk_login FOREIGN KEY (login_id) REFERENCES public.user_login(id);

