ALTER TABLE public.poker_table_user RENAME TO table_user;

ALTER TABLE public.table_user ADD CONSTRAINT table_user_fk_table FOREIGN KEY (table_id) REFERENCES public.table_profile(id) ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE public.table_user ADD CONSTRAINT table_user_fk_user FOREIGN KEY (user_id) REFERENCES public.user_profile(id) ON DELETE RESTRICT ON UPDATE CASCADE;
ALTER TABLE public.table_user ADD CONSTRAINT table_user_fk_last_game FOREIGN KEY (last_game_id) REFERENCES public.poker_game(id) ON DELETE RESTRICT ON UPDATE CASCADE;
ALTER TABLE public.table_user ADD props jsonb NULL DEFAULT NULL;
