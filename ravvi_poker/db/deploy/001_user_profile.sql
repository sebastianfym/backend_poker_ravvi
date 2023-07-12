CREATE TABLE image (
    id bigserial primary key,
    uuid uuid unique not null default uuid_generate_v4(),
    owner_id bigint references public.user_profile(id) default null,
    image_data bytea default null,
    created_ts timestamp not null default NOW()
);


ALTER TABLE user_profile
ADD COLUMN email varchar(100) default null,
ADD COLUMN image_id bigint references public.image(id) default null;


ALTER TABLE poker_table
ADD COLUMN table_type varchar(100) default null,
ADD COLUMN game_type varchar(100) default null,
ADD COLUMN table_name varchar(100) default null;
