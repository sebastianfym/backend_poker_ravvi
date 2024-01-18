DROP TABLE public.table_user;

CREATE TABLE public.table_session (
	id serial4 NOT NULL,
	table_id int8 NOT NULL,
    account_id int8 NOT NULL,
	created_ts timestamp NOT NULL DEFAULT now_utc(),
	opened_ts timestamp NULL,
	closed_ts timestamp NULL,
	CONSTRAINT table_session_pkey PRIMARY KEY (id),
	CONSTRAINT table_session_fk_table FOREIGN KEY (table_id) REFERENCES public.table_profile(id) ON DELETE CASCADE ON UPDATE CASCADE,
	CONSTRAINT table_session_fk_account FOREIGN KEY (account_id) REFERENCES public.user_account(id) ON DELETE CASCADE ON UPDATE CASCADE
);

ALTER TABLE public.table_profile ALTER COLUMN club_id SET NOT NULL;
ALTER TABLE public.table_profile ALTER COLUMN club_id SET DEFAULT 0;
