create or replace procedure create_txn_CASHOUT(in operator_id bigint, in ref_club_id bigint, in _user_id bigint, in ref_user_id bigint, in txn_value numeric, out txn_id bigint) 
language plpgsql
as $body$
declare
    member_id bigint;
    member_role varchar;
    balance_old numeric(20,2);
	balance_new numeric(20,2);
    ref_member_id bigint;
	ref_balance_new numeric(20,2);
begin
	txn_value := round(txn_value, 2);
    if txn_value<=0 then 
        RAISE EXCEPTION '1000:Invalid txn value %', txn_value;
    end if;
    -- get target player info
    select id, balance into member_id, balance_old from club_member WHERE club_id=ref_club_id and user_id=_user_id for update;
    -- check member exists
    if member_id is null then
        RAISE EXCEPTION '1002:Club % has no player %', ref_club_id, user_id;
    end if;
    balance_new := balance_old - txn_value;
    if balance_new<0 then 
        RAISE EXCEPTION '1002:Player balance % is too low for % txn', balance_old, -txn_value;
    end if;

    -- reference account
    call _txn_get_ref_balance_for_update(ref_club_id, ref_user_id, txn_value, ref_member_id, ref_balance_new);

	-- create txn
	insert into chips_txn
        (club_id, created_by, txn_type, txn_value, member_id, ref_member_id) 
		values 
        (ref_club_id, operator_id, 'CASHOUT', txn_value, member_id, ref_member_id) returning id into txn_id;

    -- create target player txn
	insert into chips_player (txn_id, member_id, delta, balance)  values (txn_id, member_id, -txn_value, balance_new);
	-- update player balance
	update club_member set balance=balance_new where id=member_id;

    call _txn_update_ref(ref_club_id, ref_member_id, txn_id, txn_value, ref_balance_new);
end;
$body$;