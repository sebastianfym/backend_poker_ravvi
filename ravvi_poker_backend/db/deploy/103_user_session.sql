create table user_session (
    id bigserial primary key,
    uuid uuid unique not null default uuid_generate_v4(),
    login_id bigint not null references user_login(id),
    created_ts timestamp not null default NOW(),
    used_ts    timestamp default NULL,
    closed_ts  timestamp default NULL
);
