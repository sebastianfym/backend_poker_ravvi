create table user_login (
    id bigserial primary key,
    uuid uuid not null default uuid_generate_v4(),    
    created timestamp not null default NOW(),
    closed timestamp default NULL,
    user_id bigint not null references user_account(id),
    device_id bigint not null references user_device(id)
);

