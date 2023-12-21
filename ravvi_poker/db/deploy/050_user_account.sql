ALTER TABLE public.club_member ALTER COLUMN created_ts SET DEFAULT now_utc();
ALTER TABLE public.club_member ADD closed_ts timestamp NULL DEFAULT NULL;
ALTER TABLE public.club_member ADD closed_by bigint NULL DEFAULT NULL;
ALTER TABLE public.club_member ADD user_comment varchar(255) NULL DEFAULT NULL;
ALTER TABLE public.club_member ADD club_comment varchar(255) NULL DEFAULT NULL;
ALTER TABLE public.club_member ADD balance numeric(20,4) NOT NULL DEFAULT 0;
ALTER TABLE public.club_member ADD balance_shared numeric(20,4) NOT NULL DEFAULT 0;

ALTER TABLE public.club_member RENAME TO user_account;

ALTER TABLE public.user_account RENAME CONSTRAINT club_member_fk_approved_by TO user_account_fk_approved_by;
ALTER TABLE public.user_account RENAME CONSTRAINT club_member_fk_club TO user_account_fk_club;
ALTER TABLE public.user_account RENAME CONSTRAINT club_member_fk_user TO user_account_fk_user;

CREATE TYPE user_role_enum AS ENUM ('P', 'O', 'M', 'A', 'S');

ALTER TABLE public.user_account ALTER COLUMN user_role TYPE public.user_role_enum USING user_role::text::public.user_role_enum;
ALTER TABLE public.user_account ALTER COLUMN user_role SET NOT NULL;
ALTER TABLE public.user_account ALTER COLUMN user_role SET DEFAULT 'P';
ALTER TABLE public.user_account ALTER COLUMN club_id SET DEFAULT 0;
