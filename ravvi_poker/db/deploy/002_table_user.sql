CREATE TABLE
  public.poker_table_user (
    table_id bigint NOT NULL, 
    user_id bigint NOT NULL,
    exit_ts TIMESTAMP WITHOUT TIME ZONE NULL,
    exit_game_id bigint NOT NULL
  )
;

ALTER TABLE
  public.poker_table_user
ADD
  CONSTRAINT poker_table_user_pkey PRIMARY KEY (table_id, user_id)
;

CREATE INDEX poker_table_user_idx ON public.poker_table_user USING btree (user_id);
