ALTER TABLE image
ALTER COLUMN image_data TYPE TEXT;

ALTER TABLE image
ADD COLUMN mime_type varchar(100) default null;
