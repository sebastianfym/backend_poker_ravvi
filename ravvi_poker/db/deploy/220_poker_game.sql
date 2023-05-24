create table poker_game (
    id bigserial primary key,
    table_id bigint not null references poker_table(id),
    begin_ts timestamp not null default NOW(),
    end_ts timestamp null
);
