create or replace procedure _txn_get_ref_balance_for_update(ref_club_id bigint, ref_user_id bigint, txn_value numeric, out ref_member_id bigint, out ref_balance_new numeric)
language plpgsql
as $body$
declare
    ref_type varchar;
    ref_member_role varchar;
	ref_balance_old numeric;
begin
    if ref_user_id is null then
        -- club reference
        ref_type := 'Club';
        ref_member_id := NULL;
        select club_balance into ref_balance_old from club_profile where id=ref_club_id for update;
    else
        -- agent reference
        ref_type := 'Agent';
        select id, user_role, balance_shared into ref_member_id, ref_member_role, ref_balance_old from club_member WHERE club_id=ref_club_id and user_id=ref_user_id for update;
        if ref_member_id is null then
            RAISE EXCEPTION '1001:Club % has no member %', ref_club_id, ref_user_id;
        end if;
        if ref_member_role not in ('A','S') then
            RAISE EXCEPTION '1002:Club % has no agent %', ref_club_id, ref_user_id;
        end if;
    end if;
    ref_balance_new := ref_balance_old + txn_value;
    if ref_balance_new<0 then 
        RAISE EXCEPTION '1003:%s balance % is too low for % txn', ref_type, ref_balance_old, -txn_value;
    end if;
end;
$body$;


create or replace procedure _txn_update_ref(ref_club_id bigint, ref_member_id bigint, txn_id bigint, txn_value numeric, ref_balance_new numeric)
language plpgsql
as $body$
begin
    if ref_member_id is null then
        -- club reference
        insert into chips_club 
            (txn_id, club_id, delta, balance) 
            values 
            (txn_id, ref_club_id, txn_value, ref_balance_new);
	    -- update club profle balance;
		update club_profile set club_balance=ref_balance_new where id=ref_club_id;
    else
        -- agent reference
        insert into chips_agent 
            (txn_id, member_id, delta, balance) 
            values 
            (txn_id, ref_member_id, txn_value, ref_balance_new);
	    -- update balance;
		update club_member set balance_shared=ref_balance_new where id=ref_member_id;
    end if;
end;
$body$;


