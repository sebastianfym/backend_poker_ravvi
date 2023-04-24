create table user_device (
    id bigserial primary key,
    uuid uuid unique not null default uuid_generate_v4(),    
    props json,
    created_ts timestamp not null default NOW(),
    closed_ts  timestamp default NULL
);

