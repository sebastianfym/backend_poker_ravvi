ALTER TABLE ONLY public.club_profile ADD COLUMN tables_сount INT DEFAULT 0, ADD COLUMN players_online INT DEFAULT 0, ADD COLUMN club_balance numeric(20,4) DEFAULT 0;

CREATE FUNCTION public.table_close_trg_proc() RETURNS trigger
    AS $$
BEGIN
  IF (SELECT tables_сount FROM public.club_profile WHERE id = NEW.club_id) > 0 THEN
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


CREATE FUNCTION public.players_online_trg_proc() RETURNS trigger
    AS $$
DECLARE
    club_id_var bigint;
BEGIN
    -- Получаем club_id из table_profile по id
    SELECT club_id INTO club_id_var FROM public.table_profile WHERE id = NEW.table_id;

    IF NEW.created_ts IS NOT NULL AND NEW.closed_ts IS NULL THEN
        UPDATE public.club_profile SET players_online = players_online + 1 WHERE id = club_id_var;
    ELSIF NEW.created_ts IS NOT NULL AND NEW.closed_ts IS NOT NULL THEN
        UPDATE public.club_profile SET players_online = players_online - 1 WHERE id = club_id_var;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;


CREATE TRIGGER players_online_trg AFTER INSERT OR UPDATE OF created_ts, closed_ts ON public.table_session FOR EACH ROW EXECUTE FUNCTION public.players_online_trg_proc();
CREATE TRIGGER table_open_trg AFTER INSERT OR UPDATE OF created_ts ON public.table_profile FOR EACH ROW EXECUTE FUNCTION public.table_open_trg_proc();
CREATE TRIGGER table_closed_trg AFTER UPDATE OF closed_ts ON public.table_profile FOR EACH ROW EXECUTE FUNCTION public.table_close_trg_proc();

