create table public.user_ws_client (
    id serial primary key,
    session_id BIGINT not null,
    created_ts timestamp not null default now_utc(),
    closed_ts TIMESTAMP null
);