CREATE TABLE debug (
    id bigserial primary key,
    uuid uuid unique not null default uuid_generate_v4(),
    user_id bigint references user_profile(id) default null,
    game_id bigint references poker_game(id) default null,
    table_id bigint references poker_table(id) default null,
    debug_message text default null,
    created_ts timestamp not null default NOW()
);
