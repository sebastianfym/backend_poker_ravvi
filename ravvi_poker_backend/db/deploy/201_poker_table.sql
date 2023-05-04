create table poker_table (
    id bigserial primary key,
    club_id bigint default null,
    created_ts timestamp not null default NOW()
);
