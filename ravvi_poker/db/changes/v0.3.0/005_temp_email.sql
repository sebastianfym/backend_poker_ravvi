CREATE TABLE temp_email (
    id bigserial primary key,
    uuid uuid unique default uuid_generate_v4(),
    user_id bigint references public.user_profile(id) not null,
    temp_email varchar(100) not null,
    created_ts timestamp without time zone default NOW(),
    closed_ts timestamp without time zone
);
