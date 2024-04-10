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