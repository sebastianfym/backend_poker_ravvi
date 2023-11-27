ALTER TABLE public.club ALTER COLUMN name DROP NOT NULL;
ALTER TABLE public.club ALTER COLUMN name SET DEFAULT NULL;
ALTER TABLE public.club ADD closed_ts timestamp NULL DEFAULT NULL;
ALTER TABLE public.club_member ADD closed_ts timestamp NULL DEFAULT NULL;
ALTER TABLE public.club_member ADD user_comment varchar(255) NULL DEFAULT NULL;
ALTER TABLE public.club_member ADD club_comment varchar(255) NULL DEFAULT NULL;

CREATE OR REPLACE FUNCTION club_name_trg_proc() RETURNS TRIGGER 
AS $$
BEGIN
  IF NEW.name IS NULL OR LENGTH(NEW.name)=0 THEN
    select CONCAT('CLUB-',NEW.id) into new.name;
  END IF;
  RETURN NEW;
END; $$
LANGUAGE plpgsql;

CREATE OR REPLACE 
TRIGGER club_name_trg
BEFORE INSERT OR UPDATE ON club
FOR EACH ROW
EXECUTE PROCEDURE club_name_trg_proc();
