create table user_login (
    id bigserial primary key,
    uuid uuid unique not null default uuid_generate_v4(),    
    user_id bigint not null references user_profile(id),
    device_id bigint not null references user_device(id),
    created_ts timestamp not null default NOW(),
    closed_ts  timestamp default NULL
);

