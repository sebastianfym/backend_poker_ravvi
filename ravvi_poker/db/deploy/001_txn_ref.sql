create or replace procedure _txn_get_ref_balance_for_update(_club_id bigint, ref_member_id bigint, txn_value numeric, out ref_balance_new numeric)
language plpgsql
as $body$
declare
    ref_club_id bigint;
    ref_type varchar;
	ref_balance_old numeric;
begin
    if ref_member_id is null then
        -- club reference
        ref_type := 'Club';
        select club_balance into ref_balance_old from club_profile where id=_club_id for update;
    else
        -- agent reference
        ref_type := 'Agent';
        select club_id, balance_shared into ref_club_id, ref_balance_old from club_member WHERE id=ref_member_id for update;
        if ref_club_id is null or ref_club_id != _club_id then
            RAISE EXCEPTION '1001:Club % has no member %', _club_id, ref_member_id;
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


