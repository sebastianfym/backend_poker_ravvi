ALTER TABLE public.poker_table_user ADD CONSTRAINT table_user_fk_table FOREIGN KEY (table_id) REFERENCES public.poker_table(id) ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE public.poker_table_user ADD CONSTRAINT table_user_fk_user FOREIGN KEY (user_id) REFERENCES public.user_profile(id) ON DELETE RESTRICT ON UPDATE CASCADE;
ALTER TABLE public.poker_table_user ADD CONSTRAINT table_user_fk_last_game FOREIGN KEY (last_game_id) REFERENCES public.poker_game(id) ON DELETE RESTRICT ON UPDATE CASCADE;
ALTER TABLE public.poker_table_user ADD props jsonb NULL DEFAULT NULL;
ALTER TABLE public.poker_table ALTER COLUMN created_ts SET DEFAULT now_utc();
