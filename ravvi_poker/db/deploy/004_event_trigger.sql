CREATE OR REPLACE FUNCTION event_notify() RETURNS trigger 
AS $$
DECLARE
  payload VARCHAR;
  x VARCHAR;
BEGIN
  SELECT json_build_object('event_id',NEW.id, 'event_type', NEW.type, 'table_id',NEW.table_id, 'client_id',NEW.client_id)::VARCHAR INTO payload;
  IF NEW.event_type<100 THEN
    SELECT pg_notify('event_cmd', payload) INTO x;
  ELSE
    SELECT pg_notify('event_msg', payload) INTO x;
  END IF;
  RETURN NULL;
END; $$
LANGUAGE plpgsql;

CREATE OR REPLACE 
TRIGGER event_trigger
AFTER INSERT ON "event" 
FOR EACH ROW
EXECUTE FUNCTION event_notify();









