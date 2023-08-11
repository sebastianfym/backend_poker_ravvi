
CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA 

CREATE TABLE club (
    id bigint NOT NULL,
    founder_id bigint NOT NULL,
    name character varying(200) NOT NULL,
    description character varying(1000) DEFAULT NULL::character varying,
    created_ts timestamp without time zone DEFAULT now() NOT NULL
);

CREATE SEQUENCE club_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE club_id_seq OWNED BY club.id;

CREATE TABLE club_member (
    id bigint NOT NULL,
    club_id bigint NOT NULL,
    user_id bigint NOT NULL,
    user_role character varying(32),
    created_ts timestamp without time zone DEFAULT now() NOT NULL,
    approved_ts timestamp without time zone,
    approved_by bigint
);

CREATE SEQUENCE club_member_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE club_member_id_seq OWNED BY club_member.id;

CREATE TABLE image (
    id bigint NOT NULL,
    uuid uuid DEFAULT uuid_generate_v4() NOT NULL,
    owner_id bigint,
    image_data bytea,
    created_ts timestamp without time zone DEFAULT now() NOT NULL
);

CREATE SEQUENCE image_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE image_id_seq OWNED BY image.id;

CREATE TABLE poker_event (
    id bigint NOT NULL,
    table_id bigint NOT NULL,
    game_id bigint,
    user_id bigint,
    event_ts timestamp without time zone DEFAULT now() NOT NULL,
    event_type integer NOT NULL,
    event_props jsonb
);

CREATE SEQUENCE poker_event_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE poker_event_id_seq OWNED BY poker_event.id;

CREATE TABLE poker_game (
    id bigint NOT NULL,
    table_id bigint NOT NULL,
    begin_ts timestamp without time zone DEFAULT now() NOT NULL,
    end_ts timestamp without time zone
);

CREATE SEQUENCE poker_game_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE poker_game_id_seq OWNED BY poker_game.id;

CREATE TABLE poker_game_user (
    game_id bigint NOT NULL,
    user_id bigint NOT NULL
);

CREATE TABLE poker_table (
    id bigint NOT NULL,
    club_id bigint,
    created_ts timestamp without time zone DEFAULT now() NOT NULL,
    table_type character varying(100) DEFAULT NULL::character varying,
    game_type character varying(100) DEFAULT NULL::character varying,
    table_name character varying(100) DEFAULT NULL::character varying,
    game_subtype character varying(100) DEFAULT NULL::character varying,
    table_seats smallint
);

CREATE SEQUENCE poker_table_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE poker_table_id_seq OWNED BY poker_table.id;

CREATE TABLE user_device (
    id bigint NOT NULL,
    uuid uuid DEFAULT uuid_generate_v4() NOT NULL,
    props jsonb,
    created_ts timestamp without time zone DEFAULT now() NOT NULL,
    closed_ts timestamp without time zone
);

CREATE SEQUENCE user_device_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE user_device_id_seq OWNED BY user_device.id;

CREATE TABLE user_login (
    id bigint NOT NULL,
    uuid uuid DEFAULT uuid_generate_v4() NOT NULL,
    user_id bigint NOT NULL,
    device_id bigint NOT NULL,
    created_ts timestamp without time zone DEFAULT now() NOT NULL,
    closed_ts timestamp without time zone
);

CREATE SEQUENCE user_login_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE user_login_id_seq OWNED BY user_login.id;

CREATE TABLE user_profile (
    id bigint NOT NULL,
    uuid uuid DEFAULT uuid_generate_v4() NOT NULL,
    username character varying(100) DEFAULT NULL::character varying,
    password_hash character varying(100) DEFAULT NULL::character varying,
    created_ts timestamp without time zone DEFAULT now() NOT NULL,
    closed_ts timestamp without time zone,
    email character varying(100) DEFAULT NULL::character varying,
    image_id bigint
);

CREATE SEQUENCE user_profile_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE user_profile_id_seq OWNED BY user_profile.id;

CREATE TABLE user_session (
    id bigint NOT NULL,
    uuid uuid DEFAULT uuid_generate_v4() NOT NULL,
    login_id bigint NOT NULL,
    created_ts timestamp without time zone DEFAULT now() NOT NULL,
    used_ts timestamp without time zone,
    closed_ts timestamp without time zone
);

CREATE SEQUENCE user_session_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE user_session_id_seq OWNED BY user_session.id;

ALTER TABLE ONLY club ALTER COLUMN id SET DEFAULT nextval('public.club_id_seq'::regclass);

ALTER TABLE ONLY club_member ALTER COLUMN id SET DEFAULT nextval('public.club_member_id_seq'::regclass);

ALTER TABLE ONLY image ALTER COLUMN id SET DEFAULT nextval('public.image_id_seq'::regclass);

ALTER TABLE ONLY poker_event ALTER COLUMN id SET DEFAULT nextval('public.poker_event_id_seq'::regclass);

ALTER TABLE ONLY poker_game ALTER COLUMN id SET DEFAULT nextval('public.poker_game_id_seq'::regclass);

ALTER TABLE ONLY poker_table ALTER COLUMN id SET DEFAULT nextval('public.poker_table_id_seq'::regclass);

ALTER TABLE ONLY user_device ALTER COLUMN id SET DEFAULT nextval('public.user_device_id_seq'::regclass);

ALTER TABLE ONLY user_login ALTER COLUMN id SET DEFAULT nextval('public.user_login_id_seq'::regclass);

ALTER TABLE ONLY user_profile ALTER COLUMN id SET DEFAULT nextval('public.user_profile_id_seq'::regclass);

ALTER TABLE ONLY user_session ALTER COLUMN id SET DEFAULT nextval('public.user_session_id_seq'::regclass);

ALTER TABLE ONLY club_member
    ADD CONSTRAINT club_member_pkey PRIMARY KEY (id);

ALTER TABLE ONLY club
    ADD CONSTRAINT club_pkey PRIMARY KEY (id);

ALTER TABLE ONLY image
    ADD CONSTRAINT image_pkey PRIMARY KEY (id);

ALTER TABLE ONLY image
    ADD CONSTRAINT image_uuid_key UNIQUE (uuid);

ALTER TABLE ONLY poker_event
    ADD CONSTRAINT poker_event_pkey PRIMARY KEY (id);

ALTER TABLE ONLY poker_game
    ADD CONSTRAINT poker_game_pkey PRIMARY KEY (id);

ALTER TABLE ONLY poker_game_user
    ADD CONSTRAINT poker_game_user_pkey PRIMARY KEY (game_id, user_id);

ALTER TABLE ONLY poker_table
    ADD CONSTRAINT poker_table_pkey PRIMARY KEY (id);

ALTER TABLE ONLY user_device
    ADD CONSTRAINT user_device_pkey PRIMARY KEY (id);

ALTER TABLE ONLY user_device
    ADD CONSTRAINT user_device_uuid_key UNIQUE (uuid);

ALTER TABLE ONLY user_login
    ADD CONSTRAINT user_login_pkey PRIMARY KEY (id);

ALTER TABLE ONLY user_login
    ADD CONSTRAINT user_login_uuid_key UNIQUE (uuid);

ALTER TABLE ONLY user_profile
    ADD CONSTRAINT user_profile_pkey PRIMARY KEY (id);

ALTER TABLE ONLY user_profile
    ADD CONSTRAINT user_profile_uuid_key UNIQUE (uuid);

ALTER TABLE ONLY user_session
    ADD CONSTRAINT user_session_pkey PRIMARY KEY (id);

ALTER TABLE ONLY user_session
    ADD CONSTRAINT user_session_uuid_key UNIQUE (uuid);

CREATE INDEX club_member_idx1 ON club_member USING btree (user_id);

CREATE UNIQUE INDEX club_member_unq ON club_member USING btree (club_id, user_id);

CREATE INDEX poker_game_user_idx1 ON poker_game_user USING btree (user_id);

ALTER TABLE ONLY club_member
    ADD CONSTRAINT club_member_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES user_profile(id);

ALTER TABLE ONLY club_member
    ADD CONSTRAINT club_member_club_id_fkey FOREIGN KEY (club_id) REFERENCES club(id);

ALTER TABLE ONLY club_member
    ADD CONSTRAINT club_member_user_id_fkey FOREIGN KEY (user_id) REFERENCES user_profile(id);

ALTER TABLE ONLY image
    ADD CONSTRAINT image_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES user_profile(id);

ALTER TABLE ONLY poker_event
    ADD CONSTRAINT poker_event_game_id_fkey FOREIGN KEY (game_id) REFERENCES poker_game(id);

ALTER TABLE ONLY poker_event
    ADD CONSTRAINT poker_event_table_id_fkey FOREIGN KEY (table_id) REFERENCES poker_table(id);

ALTER TABLE ONLY poker_event
    ADD CONSTRAINT poker_event_user_id_fkey FOREIGN KEY (user_id) REFERENCES user_profile(id);

ALTER TABLE ONLY poker_game
    ADD CONSTRAINT poker_game_table_id_fkey FOREIGN KEY (table_id) REFERENCES poker_table(id);

ALTER TABLE ONLY poker_game_user
    ADD CONSTRAINT poker_game_user_game_id_fkey FOREIGN KEY (game_id) REFERENCES poker_game(id);

ALTER TABLE ONLY poker_game_user
    ADD CONSTRAINT poker_game_user_user_id_fkey FOREIGN KEY (user_id) REFERENCES user_profile(id);

ALTER TABLE ONLY user_login
    ADD CONSTRAINT user_login_device_id_fkey FOREIGN KEY (device_id) REFERENCES user_device(id);

ALTER TABLE ONLY user_login
    ADD CONSTRAINT user_login_user_id_fkey FOREIGN KEY (user_id) REFERENCES user_profile(id);

ALTER TABLE ONLY user_profile
    ADD CONSTRAINT user_profile_image_id_fkey FOREIGN KEY (image_id) REFERENCES image(id);

ALTER TABLE ONLY user_session
    ADD CONSTRAINT user_session_login_id_fkey FOREIGN KEY (login_id) REFERENCES user_login(id);

