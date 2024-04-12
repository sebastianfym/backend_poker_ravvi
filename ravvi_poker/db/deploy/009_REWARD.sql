create or replace procedure create_txn_REWARD(in _member_id bigint, in _table_session_id bigint, in txn_value numeric, out txn_id bigint) 
language plpgsql
as $body$
declare
    _club_id bigint;
    _table_id bigint;
    balance_old numeric (20,2);
	balance_new numeric(20,2);
begin
    -- round and validate txn value
	txn_value := round(txn_value, 2);
    if txn_value<=0 then 
        RAISE EXCEPTION '1000:Invalid txn value %', txn_value;
    end if;
    -- get & lock target member
    select club_id, balance into _club_id, balance_old from club_member WHERE id=_member_id for update;
    -- check member in expected club
    if _club_id is NULL then
        RAISE EXCEPTION '1001:Unknown member %', _member_id;
    end if;
    -- calc new balance
    balance_new := balance_old + txn_value;
    -- get & lock target session
    select table_id into _table_id from table_session WHERE id=_table_session_id for update;
    -- check member in expected club
    if _table_id is NULL then
        RAISE EXCEPTION '1001:Unknown table session %', _table_session_id;
    end if;

	-- create txn
	insert into chips_txn
        (club_id, created_by, txn_type, txn_value, member_id, ref_table_id) 
		values 
        (_club_id, 0, 'REWARD', txn_value, _member_id, _table_id) returning id into txn_id;
    -- create target player txn
	insert into chips_player (txn_id, member_id, delta, balance)  values (txn_id, _member_id, txn_value, balance_new);
	-- update player balance
	update club_member set balance=balance_new where id=_member_id;
end;
$body$;