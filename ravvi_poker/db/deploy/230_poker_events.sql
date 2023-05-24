create table poker_event (
    id bigserial primary key,
    table_id bigint not null references poker_table(id),
    game_id bigint null references poker_game(id),
    user_id bigint null references user_profile(id),
    event_ts timestamp not null default NOW(),
    event_type int not null,
    event_props jsonb
);
