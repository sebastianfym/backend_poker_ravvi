ALTER TABLE public.club ADD closed_ts timestamp NULL DEFAULT NULL;
ALTER TABLE public.club_member ADD closed_ts timestamp NULL DEFAULT NULL;
ALTER TABLE public.club_member ADD user_comment varchar(255) NULL DEFAULT NULL;
ALTER TABLE public.club_member ADD club_comment varchar(255) NULL DEFAULT NULL;
