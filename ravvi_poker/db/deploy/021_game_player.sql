ALTER TABLE public.poker_game_user RENAME TO game_player;

ALTER TABLE public.game_player RENAME CONSTRAINT poker_game_user_game_id_fkey TO game_player_fk_game;
ALTER TABLE public.game_player RENAME CONSTRAINT poker_game_user_user_id_fkey TO game_player_fk_user;
