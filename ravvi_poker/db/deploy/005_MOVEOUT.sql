create or replace procedure create_txn_MOVEOUT(in operator_id bigint, in _club_id bigint, in _user_id bigint, in ref_user_id bigint, in txn_value numeric, out txn_id bigint) 
language plpgsql
as $body$
declare
    member_id bigint;
    member_role varchar;
    balance_old numeric (20,2);
	balance_new numeric(20,2);
    ref_member_id bigint;
	ref_balance_new numeric(20,2);
begin
	txn_value := round(txn_value, 2);
    if txn_value<=0 then 
        RAISE EXCEPTION '1000:Invalid txn value %', txn_value;
    end if;
    -- get target member
    select id, user_role, balance_shared into member_id, member_role, balance_old from club_member WHERE club_id=_club_id and user_id=_user_id for update;
    -- check member exists and have agent role
    if member_id is null then
        RAISE EXCEPTION '1001:Club % has no member %', _club_id, _user_id;
    end if;
    if member_role not in ('A','S') then
        RAISE EXCEPTION '1002:Club % has no agent %', _club_id, _user_id;
    end if;
    balance_new := balance_old - txn_value;
    if balance_new<0 then 
        RAISE EXCEPTION '1003:Agent balance % is too low for % txn', balance_old, -txn_value;
    end if;

    call _txn_get_ref_balance_for_update(_club_id, ref_user_id, txn_value, ref_member_id, ref_balance_new);
    
	-- create txn
	insert into chips_txn
        (club_id, created_by, txn_type, txn_value, member_id, ref_member_id) 
		values 
        (_club_id, operator_id, 'MOVEOUT', txn_value, member_id, ref_member_id) returning id into txn_id;

    -- create target agent txn
	insert into chips_agent (txn_id, member_id, delta, balance)  values (txn_id, member_id, txn_value, balance_new);
	-- update agent balance
	update club_member set balance_shared=balance_new where id=member_id;

    -- create ref txn and update balance
    call _txn_update_ref(_club_id, ref_member_id, txn_id, txn_value, ref_balance_new);
end;
$body$;