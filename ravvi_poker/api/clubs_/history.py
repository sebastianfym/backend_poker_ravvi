from starlette.status import HTTP_200_OK
from fastapi import Request, Depends
from .utilities import check_rights_user_club_owner_or_manager
from ...db import DBI
from ..utils import SessionUUID, get_session_and_user
from .router import router
from .types import *


@router.get("/{club_id}/club_txn_history", status_code=HTTP_200_OK, summary='Получить внутреклубные транзакции произошедшие в клубе',
            responses={
                404: {"model": ErrorException, "detail": "Club not found",
                      "message": "Member not found"},
                403: {"model": ErrorException, "detail": "Permission denied",
                      "message": "You dont have permissions for that action"}
            }
            )
async def v1_club_txn_history(club_id: int, users=Depends(check_rights_user_club_owner_or_manager)) -> List[ClubHistoryTransaction]:
    """
    Служит для получения внутреклубных транзакций произошедших в клубе

    - **club_id**: number

    """
    async with DBI() as db:
        all_club_members = [member for member in await db.get_club_members(club_id)]
        if len(all_club_members) == 0:
            return []
        result_list = []
        for member in all_club_members:
            all_member_txns = await db.get_all_account_txn(member.id)  # Возвращает список id транзакций
            recipient = await db.get_club_member(member.id)

            member_user_profile = await db.get_user(recipient.user_id)

            for txn in all_member_txns:
                if txn.txn_type in ["REWARD", "BUYIN"]:
                    continue
                try:
                    sender = await db.get_club_member(txn.sender_id)
                    sender_user_profile = await db.get_user(sender.user_id)
                    member_user = await db.get_user(id=member.user_id)
                    txn_model = ClubHistoryTransaction(
                        txn_type=txn.txn_type,
                        txn_value=-txn.txn_value,
                        txn_time=txn.created_ts.timestamp(),
                        recipient_id=member_user.id,
                        recipient_name=member_user_profile.name,
                        recipient_nickname=recipient.nickname,
                        recipient_country=member_user_profile.country,
                        recipient_role=recipient.user_role,
                        sender_id=txn.sender_id,
                        sender_name=sender_user_profile.name,
                        sender_nickname=sender.nickname,
                        sender_country=sender_user_profile.country,
                        sender_role=sender.user_role,
                        balance_type=txn.props.get('balance_type', None)
                    )
                    result_list.append(txn_model)
                except AttributeError as error:
                    # log.info_(f"Error getting club. Error: {error}")
                    continue
    return result_list


@router.get("/{club_id}/history", status_code=HTTP_200_OK, summary="Getting the transaction history of a club member",
            responses={
                404: {"model": ErrorException, "detail": "Club not found",
                      "message": "Member not found"},
                403: {"model": ErrorException, "detail": "Permission denied",
                      "message": "You dont have permissions for that action"}
            }
            )
async def v1_get_history_trx(club_id: int, session_uuid: SessionUUID) -> List[TxnHistoryManual | TxnHistoryOnTable]:
    """
    Служит для получения всех транзакций произошедших в клубе

    - **club_id**: number

    """
    async with (DBI() as db):
        _, user = await get_session_and_user(db, session_uuid)
        txn_history = await db.get_user_history_trx_in_club(user.id, club_id)

        txn_list = []
        for txn in txn_history:
            if txn.txn_value == 00.00:
                continue
            txn = txn._asdict()
            sender_account = await db.get_club_member(member_id=txn['sender_id'])
            if txn['txn_type'] not in ["REPLENISHMENT", "CASHOUT", "BUYIN", "CHIPSIN", "CHIPSOUT"]: #"CASHOUT", "BUYIN",
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
                    txn_time=txn['created_ts'].timestamp(),
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
                        txn_time=txn['created_ts'].timestamp(),
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
