create table club (
    id bigserial primary key,
    founder_id bigint not null,
    name varchar(200) not null,
    description varchar(1000) default null,
    created_ts timestamp not null default NOW()
);
