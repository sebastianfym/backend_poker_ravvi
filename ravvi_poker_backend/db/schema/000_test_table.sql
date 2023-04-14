create table test_table (
    id serial primary key,
    created_at timestamp not null default NOW()
);