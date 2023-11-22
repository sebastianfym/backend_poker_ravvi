ALTER TABLE public.poker_table RENAME TO table_profile;
ALTER TABLE public.table_profile RENAME COLUMN game_settings TO props;
ALTER TABLE public.table_profile ALTER COLUMN created_ts SET DEFAULT now_utc();
