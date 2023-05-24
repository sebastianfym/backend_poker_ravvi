create table poker_game_user (
    game_id bigint not null references poker_game(id),
    user_id bigint not null references user_profile(id),
    PRIMARY KEY (game_id, user_id)  
);

create index poker_game_user_idx1 ON poker_game_user (user_id);
