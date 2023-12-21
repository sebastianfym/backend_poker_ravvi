ALTER TABLE public.club ALTER COLUMN name DROP NOT NULL;
ALTER TABLE public.club ALTER COLUMN name SET DEFAULT NULL;
ALTER TABLE public.club ADD closed_ts timestamp NULL DEFAULT NULL;
ALTER TABLE public.club ADD service_balance numeric(18,2) NOT NULL DEFAULT 0;
ALTER TABLE public.club ADD service_limit numeric(18,2) NOT NULL DEFAULT 0;
ALTER TABLE public.club DROP COLUMN founder_id;
ALTER TABLE public.club RENAME TO club_profile;

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
BEFORE INSERT OR UPDATE ON club_profile
FOR EACH ROW
EXECUTE PROCEDURE club_name_trg_proc();
