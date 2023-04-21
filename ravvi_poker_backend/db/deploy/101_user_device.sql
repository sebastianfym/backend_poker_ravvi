create table user_device (
    id bigserial primary key,
    uuid uuid not null default uuid_generate_v4(),    
    created timestamp not null default NOW(),
    props json
);

