ALTER TABLE ONLY public.club_profile ADD COLUMN tables_сount INT DEFAULT 0, ADD COLUMN players_online INT DEFAULT 0;

CREATE FUNCTION public.table_close_trg_proc() RETURNS trigger
    AS $$
BEGIN
  IF NEW.closed_ts IS NOT NULL AND OLD.closed_ts IS DISTINCT FROM NEW.closed_ts THEN
    UPDATE public.club_profile SET tables_сount = tables_сount - 1 WHERE id = NEW.club_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE FUNCTION public.table_open_trg_proc() RETURNS trigger
    AS $$
BEGIN
  IF NEW.created_ts IS NOT NULL AND NEW.closed_ts IS NULL THEN
    UPDATE public.club_profile SET tables_сount = tables_сount + 1 WHERE id = NEW.club_id;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER table_open_trg AFTER INSERT OR UPDATE OF created_ts ON public.table_profile FOR EACH ROW EXECUTE FUNCTION public.table_open_trg_proc();
CREATE TRIGGER table_closed_trg AFTER UPDATE OF closed_ts ON public.table_profile FOR EACH ROW EXECUTE FUNCTION public.table_close_trg_proc();


