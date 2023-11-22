ALTER TABLE public.poker_game RENAME TO game_profile;
ALTER TABLE public.game_profile RENAME CONSTRAINT poker_game_table_id_fkey TO game_profile_fk_table;
ALTER TABLE public.game_profile ALTER COLUMN begin_ts SET DEFAULT now_utc();
ALTER TABLE public.game_profile ADD props jsonb NULL;

