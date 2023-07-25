ALTER TABLE club
ADD COLUMN image_id bigint references public.image(id) default null;
