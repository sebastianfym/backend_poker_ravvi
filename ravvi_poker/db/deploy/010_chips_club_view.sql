CREATE OR REPLACE VIEW chips_club_view
AS 
select
    cc.club_id,
    cc.txn_id,
    tx.created_ts,
    tx.created_by,
    tx.txn_type,
    cc.delta txn_delta,
    cc.balance,
    m.user_id
from chips_club cc 
join chips_txn tx on tx.id=cc.txn_id
left join club_member m on m.id=tx.member_id;

CREATE OR REPLACE VIEW chips_player_view
AS 
select
    cp.member_id,
    cp.txn_id,
    tx.created_ts,
    tx.created_by,
    tx.txn_type,
    cp.delta txn_delta,
    cp.balance,
    m.user_id,
    tx.ref_table_id
from chips_player cp 
join chips_txn tx on tx.id=cp.txn_id
left join club_member m on m.id=cp.member_id;
