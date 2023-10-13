CREATE TABLE
  public.poker_table_user (table_id bigint NOT NULL, user_id bigint NOT NULL)
;

ALTER TABLE
  public.poker_table_user
ADD
  CONSTRAINT poker_table_user_pkey PRIMARY KEY (table_id)
;