CREATE OR REPLACE FUNCTION poker_event_notify() RETURNS trigger 
AS $$
DECLARE
  payload VARCHAR;
  x VARCHAR;
BEGIN
  SELECT json_build_object('id',NEW.id, 'table_id',NEW.table_id, 'client_id',NEW.client_id, 'type', NEW.event_type)::VARCHAR INTO payload;
  IF NEW.event_type<100 THEN
    SELECT pg_notify('poker_event_cmd', payload) INTO x;
  ELSE
    SELECT pg_notify('poker_event_msg', payload) INTO x;
  END IF;
  RETURN NULL;
END; $$
LANGUAGE plpgsql;

CREATE OR REPLACE 
TRIGGER poker_event_trigger
AFTER INSERT ON poker_event 
FOR EACH ROW
EXECUTE FUNCTION poker_event_notify();









