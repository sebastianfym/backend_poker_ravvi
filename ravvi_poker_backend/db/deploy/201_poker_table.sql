create table poker_table (
    id bigserial primary key,
    created_ts timestamp not null default NOW()
);
