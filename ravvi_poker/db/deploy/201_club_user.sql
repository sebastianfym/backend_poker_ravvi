create table club_user (
    id bigserial primary key,
    club_id bigint not null references club(id),
    user_id bigint not null references user_profile(id),
    user_role varchar(32),
    created_ts timestamp not null default NOW(),
    approved_ts timestamp default null,
    approved_by bigint null references user_profile(id)
);

create unique index club_user_unq ON club_user (club_id, user_id);
create index club_user_idx1 ON club_user (user_id);
