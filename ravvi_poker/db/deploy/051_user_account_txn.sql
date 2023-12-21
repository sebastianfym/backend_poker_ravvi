CREATE TABLE public.user_account_txn (
	id serial4 NOT NULL,
    created_ts timestamp without time zone DEFAULT now_utc() NOT NULL,
    account_id int8 NOT NULL,
    txn_type VARCHAR(30) NOT NULL,
    txn_value numeric(20,4) NOT NULL,
    props jsonb,
    CONSTRAINT user_account_txn_pkey PRIMARY KEY (id)
);

ALTER TABLE ONLY public.user_account_txn
    ADD CONSTRAINT user_account_txn_fk_account FOREIGN KEY (account_id) REFERENCES public.user_account(id);
