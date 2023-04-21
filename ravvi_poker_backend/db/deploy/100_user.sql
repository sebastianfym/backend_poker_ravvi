create table user_account (
    id bigserial primary key,
    uuid uuid not null default uuid_generate_v4(),    
    created timestamp not null default NOW(),
    username varchar(100) default null,
    password varchar(100) default null
);

