ALTER TABLE public.poker_game RENAME TO game;
ALTER TABLE public.poker_game_user RENAME TO game_user;

ALTER TABLE public.game RENAME CONSTRAINT poker_game_table_id_fkey TO game_fk_table;
ALTER TABLE public.game_user RENAME CONSTRAINT poker_game_user_game_id_fkey TO game_user_fk_game;
ALTER TABLE public.game_user RENAME CONSTRAINT poker_game_user_user_id_fkey TO game_user_fk_user;
