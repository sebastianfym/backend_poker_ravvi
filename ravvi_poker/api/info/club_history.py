from starlette.status import HTTP_200_OK

from ravvi_poker.api.info.types import TxnHistoryOnTable, TxnHistoryManual
from ravvi_poker.db import DBI
from .router import router
from ..utils import SessionUUID, get_session_and_user


@router.get("/{club_id}/history", status_code=HTTP_200_OK,
            summary="Getting the transaction history of a club member")
async def v1_get_history_trx(club_id: int, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        txn_history = await db.get_user_history_trx_in_club(user.id, club_id)

        txn_list = []
        for txn in txn_history:
            if txn.txn_value == 00.00:
                continue
            txn = txn._asdict()
            sender_account = await db.get_club_member(member_id=txn['sender_id'])
            if txn['txn_type'] not in ["REPLENISHMENT", "BUYIN", "CHIPSIN", "CHIPSOUT"]: #"CASHOUT", "BUYIN", CASHOUT
                try:
                    username = (await db.get_user(sender_account.user_id)).name
                    role = (await db.find_account(user_id=sender_account.user_id, club_id=club_id)).user_role
                    image_id = (await db.get_user(sender_account.user_id)).image_id
                except (ValueError, AttributeError):
                    username = "Undefined username"
                    role = "Undefined role"
                    image_id = None

                txn_manual = TxnHistoryManual(
                    username=username,
                    sender_id=txn['sender_id'],
                    txn_time=float(txn['created_ts'].timestamp()),
                    txn_type=txn['txn_type'],
                    txn_value=txn['txn_value'],
                    balance=txn['total_balance'],
                    role=role,
                    image_id=image_id
                )
                txn_list.append(txn_manual)

            else:
                if txn['txn_type'] in ["REPLENISHMENT"]:#, "CHIPSIN"]:
                    continue
                try:
                    table_info = await db.get_table(txn['props'].get('table_id'))
                    txn_table = TxnHistoryOnTable(
                        table_name=table_info.table_name,
                        table_id=table_info.id,
                        txn_time=float(txn['created_ts'].timestamp()),
                        min_blind=table_info.props['blind_small'],
                        max_blind=table_info.props['blind_big'],
                        txn_type=txn['txn_type'],
                        txn_value=txn['txn_value'],
                        balance=txn['total_balance']
                    )
                    txn_list.append(txn_table)
                except AttributeError:
                    continue
        return txn_list