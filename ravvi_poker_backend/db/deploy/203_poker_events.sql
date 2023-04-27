create table poker_events (
    id bigserial primary key,
    game_id bigint not null references poker_table(id),
    user_id bigint not null references user_profile(id),
    event_ts timestamp not null default NOW(),
    event_type int not null,
    event_props json
);
