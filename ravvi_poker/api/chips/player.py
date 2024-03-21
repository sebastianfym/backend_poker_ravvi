import decimal
from decimal import Decimal
from datetime import datetime as DateTime
from fastapi import APIRouter, Request, Depends, HTTPException, Response
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_409_CONFLICT
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY
from pydantic import BaseModel, Field, field_validator, validator

from .utilities import check_rights_user_club_owner_or_manager
from ...db import DBI
from ..utils import SessionUUID, get_session_and_user
# from ..types import HTTPError
from .types import ChipsParams, ChipsTxnItem, ChipsParamsForMembers, ErrorException

from .router import router


@router.post("/{club_id}/players/chips", status_code=HTTP_201_CREATED,
             responses={
                 400: {"model": ErrorException, "detail": "Quantity club members for action is invalid"},
                 409: {"model": ErrorException, "detail": "Invalid amount value"},
                 404: {"model": ErrorException, "detail": "Club or user not found"},
             },
             summary="Пополнить или списать фишки с баланса пользователя/ей")
async def v1_club_chips(club_id: int, params: ChipsParamsForMembers, session_uuid: SessionUUID): #-> ChipsTxnItem: # user_id: int,
    """
    Пополнение или списание фишек с баланса пользователей на баланс клуба.

    - **amount**: number > 0 | number < 0 | "all"
    - **club_member**: list
    [
        {
            - **id**: number
            - **balance**: number | null
            - **balance_shared**: number | null
        }
    ]

    Возвращает status code == 200
    """
    members_list = params.club_member
    if len(members_list) == 0:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='Quantity club members for action is invalid')

    amount = params.amount
    if isinstance(amount, str) and amount != 'all':
        raise HTTPException(status_code=HTTP_409_CONFLICT, detail='Invalid amount value')

    async with DBI() as db:
        club_owner_account, user, club = await check_rights_user_club_owner_or_manager(club_id, session_uuid)
        # if mode == 'pick_up':
        if amount == "all" or amount < 0:
            mode = 'pick_up'
            if amount == "all":
                for member in members_list:
                    account = await db.find_account(user_id=member['id'], club_id=club_id)
                    if member['balance'] is None and member['balance_shared'] is None:
                        continue
                    elif member['balance'] is None and (member['balance_shared'] or member["balance_shared"] == 0):
                        balance_shared = await db.delete_all_chips_from_the_agent_balance(account.id, user.id)
                        await db.refresh_club_balance(club_id, balance_shared.balance_shared, mode)

                    elif (member['balance'] or member["balance"] == 0) and member['balance_shared'] is None:
                        balance = await db.delete_all_chips_from_the_account_balance(account.id, user.id)
                        await db.refresh_club_balance(club_id, balance.balance, mode)

                    elif (member['balance'] or member["balance"] == 0) and (
                            member['balance_shared'] or member["balance_shared"] == 0):
                        balance_shared = await db.delete_all_chips_from_the_agent_balance(account.id, user.id)
                        balance = await db.delete_all_chips_from_the_account_balance(account.id, user.id)
                        await db.refresh_club_balance(club_id, balance.balance + balance_shared.balance_shared, mode)
            else:
                amount = round(decimal.Decimal(amount / len(members_list)), 2)
                for member in members_list:
                    account = await db.find_account(user_id=member['id'], club_id=club_id)
                    if member['balance'] is None and member['balance_shared'] is None:
                        continue
                    elif member['balance'] is None and (member['balance_shared'] or member["balance_shared"] == 0):
                        balance_shared = await db.delete_chips_from_the_agent_balance(abs(amount), account.id, user.id)
                        await db.refresh_club_balance(club_id, balance_shared[0].balance_shared, mode)

                    elif (member['balance'] or member["balance"] == 0) and member['balance_shared'] is None:
                        balance = await db.delete_chips_from_the_account_balance(abs(amount), account.id, user.id)
                        await db.refresh_club_balance(club_id, balance.balance, mode)

                    elif (member['balance'] or member["balance"] == 0) and (member['balance_shared'] or member["balance_shared"] == 0):
                        balance = await db.delete_chips_from_the_account_balance(abs(amount), account.id, user.id)
                        balance_shared = await db.delete_chips_from_the_agent_balance(abs(amount), account.id, user.id)
                        await db.refresh_club_balance(club_id, balance.balance + balance_shared[0].balance_shared, mode)
            return HTTP_200_OK

        # elif mode == 'give_out':
        elif amount > 0:
            balance_count = 0
            balance_shared_count = 0
            mode = 'give_out'
            for check_balance in members_list:
                if check_balance['balance'] is None:
                    balance_count = balance_count
                elif check_balance['balance'] >= 0:
                    balance_count += 1
                if check_balance['balance_shared'] is None:
                    balance_shared_count = balance_shared_count
                elif check_balance['balance_shared'] >= 0:
                    balance_shared_count += 1

            if (club.club_balance < amount) or (club.club_balance - amount < 0):
                raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='Club balance cannot be less than request amount')
            amount = round(decimal.Decimal(amount / len(members_list)), 2)
            for member in members_list:
                account = await db.find_account(user_id=member['id'], club_id=club_id)
                if member['balance'] is None and member['balance_shared'] is None:
                    continue
                elif member['balance'] is None and (member['balance_shared'] or member["balance_shared"] == 0):
                    await db.giving_chips_to_the_user(amount, account.id, "balance_shared", user.id)#club_owner_account.id)
                    await db.refresh_club_balance(club_id, amount, mode)
                elif (member['balance'] or member["balance"] == 0) and member['balance_shared'] is None:
                    await db.giving_chips_to_the_user(amount, account.id, "balance", user.id)#club_owner_account.id)
                    await db.refresh_club_balance(club_id, amount, mode)
                elif (member['balance'] or member["balance"] == 0) and (member['balance_shared'] or member["balance_shared"] == 0):
                    await db.giving_chips_to_the_user(amount, account.id, "balance", user.id)#club_owner_account.id)
                    await db.giving_chips_to_the_user(amount, account.id, "balance_shared", user.id)#club_owner_account.id)
                    await db.refresh_club_balance(club_id, amount * 2, mode)
            return HTTP_200_OK

        else:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='Invalid mode value')



@router.post("/{club_id}/players/rakeback/{user_id}", status_code=HTTP_201_CREATED,
             # responses={
             #     400: {"model": HTTPError, "description": "Invalid params values"},
             #     403: {"model": HTTPError, "description": "No access for requested operation"},
             #     404: {"model": HTTPError, "description": "Club or player not found"},
             # },
             summary="Send rakeback to player")
async def v1_club_chips(club_id: int, user_id: int, params: ChipsParams, session_uuid: SessionUUID) -> ChipsTxnItem:
    """
    Send rakeback to player

    - **amount**: operation amount, where amount>0

    Returns agent chips transaction info

    - **id**: txn id
    - **created_ts**: operation timestamp
    - **created_by**: requestor user_id
    - **txn_type**: RAKEBACK
    - **amount**: chips amount
    - **balance**: new club balance after the operation completed

    """
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        member = await db.find_account(club_id=club_id, user_id=user.id)
        if not member or member.user_role != "O":
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="No access")

    created_ts = DateTime.utcnow().replace(microsecond=0).timestamp()
    return ChipsTxnItem(id=1,
                        created_ts=created_ts,
                        created_by=user.id,
                        txn_type='RAKEBACK',
                        amount=params.amount,
                        balance=params.amount
                        )