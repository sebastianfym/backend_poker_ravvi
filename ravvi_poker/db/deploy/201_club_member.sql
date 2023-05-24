create table club_member (
    id bigserial primary key,
    club_id bigint not null references club(id),
    user_id bigint not null references user_profile(id),
    user_role varchar(32),
    created_ts timestamp not null default NOW(),
    approved_ts timestamp default null,
    approved_by bigint null references user_profile(id)
);

create unique index club_member_unq ON club_member (club_id, user_id);
create index club_member_idx1 ON club_member (user_id);
