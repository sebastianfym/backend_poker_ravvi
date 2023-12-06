ALTER TABLE public.user_login RENAME CONSTRAINT user_login_device_id_fkey TO login_fk_device;
ALTER TABLE public.user_login RENAME CONSTRAINT user_login_user_id_fkey TO login_fk_user;
ALTER TABLE public.club RENAME CONSTRAINT club_image_id_fkey TO club_fk_image;
ALTER TABLE public.club_member RENAME CONSTRAINT club_member_club_id_fkey TO club_member_fk_club;
ALTER TABLE public.club_member RENAME CONSTRAINT club_member_user_id_fkey TO club_member_fk_user;
ALTER TABLE public.club_member RENAME CONSTRAINT club_member_approved_by_fkey TO club_member_fk_approved_by;
