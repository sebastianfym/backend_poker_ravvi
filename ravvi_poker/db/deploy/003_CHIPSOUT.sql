create or replace procedure create_txn_CHIPSOUT(in operator_id bigint, in club_id bigint, in txn_value numeric, out txn_id bigint) 
language plpgsql
as $body$
declare
    club_closed_ts timestamp;
	club_balance_old numeric(20,2);
	club_balance_new numeric(20,2);
begin
	txn_value := round(txn_value, 2);
    if txn_value<=0 then 
        RAISE EXCEPTION '1000:Invalid txn value %', txn_value;
    end if;
    -- get club balance
	select club_balance, closed_ts into club_balance_old, club_closed_ts from club_profile where id=club_id for update;
    if club_balance_old is null then
        RAISE EXCEPTION '1000:Club % not found', club_id;
    end if;
    club_balance_new := club_balance_old - txn_value;
    if club_balance_new<0 then 
        RAISE EXCEPTION '1001:Club balance % is too low for % txn', club_balance_old, -txn_value;
    end if;
	-- create txn
	insert into chips_txn 
        (club_id, created_by, txn_type, txn_value) 
		values 
        (club_id, operator_id, 'CHIPSOUT', txn_value) returning id into txn_id;
	-- create club record
	insert into chips_club 
        (txn_id, club_id, delta, balance) 
		values 
        (txn_id, club_id, -txn_value, club_balance_new);
    -- update club profle balance
	update club_profile set club_balance=club_balance_new where id=club_id;
end;
$body$;