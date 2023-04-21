create table user_session (
    id bigserial primary key,
    uuid uuid not null default uuid_generate_v4(),
    created timestamp not null default NOW(),
    closed timestamp default NULL,
    user_login_id bigint not null references user_login(id)
);
