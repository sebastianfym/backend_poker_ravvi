create table user_profile (
    id bigserial primary key,
    uuid uuid unique not null default uuid_generate_v4(),    
    username varchar(100) default null,
    email varchar(100) default null,
    password_hash varchar(100) default null,
    photo varchar(100) default null,
    created_ts timestamp not null default NOW(),
    closed_ts  timestamp default NULL
);
