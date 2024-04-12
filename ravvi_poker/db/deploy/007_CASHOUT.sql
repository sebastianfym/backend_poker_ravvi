create or replace procedure create_txn_CASHOUT(in operator_id bigint, in _club_id bigint, in _member_id bigint, in ref_member_id bigint, in txn_value numeric, out txn_id bigint) 
language plpgsql
as $body$
declare
    x_club_id bigint;
    balance_old numeric (20,2);
	balance_new numeric(20,2);
	ref_balance_new numeric(20,2);
begin
    -- round and validate txn value
	txn_value := round(txn_value, 2);
    if txn_value<=0 then 
        RAISE EXCEPTION '1000:Invalid txn value %', txn_value;
    end if;
    -- get & lock club
	select id into x_club_id from club_profile where id=_club_id for update;
    if x_club_id is null then
        RAISE EXCEPTION '1000:Club % not found', club_id;
    end if;
    -- get & lock target member
    select club_id, balance into x_club_id, balance_old from club_member WHERE id=_member_id for update;
    -- check member in expected club
    if x_club_id is NULL or x_club_id!=_club_id then
        RAISE EXCEPTION '1001:Club % has no member %', _club_id, _member_id;
    end if;
    -- calc new balance
    balance_new := balance_old - txn_value;
    if balance_new<0 then 
        RAISE EXCEPTION '1003:Agent balance % is too low for % txn', balance_old, -txn_value;
    end if;

    -- get & lock reference account
    call _txn_get_ref_balance_for_update(_club_id, ref_member_id, txn_value, ref_balance_new);
    
	-- create txn
	insert into chips_txn
        (club_id, created_by, txn_type, txn_value, member_id, ref_member_id) 
		values 
        (_club_id, operator_id, 'CASHOUT', txn_value, _member_id, ref_member_id) returning id into txn_id;
    -- create target agent txn
	insert into chips_player (txn_id, member_id, delta, balance)  values (txn_id, _member_id, -txn_value, balance_new);
	-- update agent balance
	update club_member set balance=balance_new where id=_member_id;

    -- create ref txn and update balance
    call _txn_update_ref(_club_id, ref_member_id, txn_id, txn_value, ref_balance_new);
end;
$body$;