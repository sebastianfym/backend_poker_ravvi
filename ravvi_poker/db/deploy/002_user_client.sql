create table "public"."user_client" (
    id serial primary key,
    session_id BIGINT not null,
    opened_ts timestamp not null default now_utc(),
    closed_ts TIMESTAMP null
);