from decimal import Decimal
from datetime import datetime as DateTime
from fastapi import APIRouter, Request, Depends, HTTPException, Response
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_418_IM_A_TEAPOT
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY
from pydantic import BaseModel, Field, field_validator, validator

from .utilities import check_rights_user_club_owner_or_manager
from ...db import DBI
from ..utils import SessionUUID, get_session_and_user
# from ..types import HTTPError
from .types import ChipsParams, ChipsTxnItem

from .router import router


@router.post("/{club_id}/club/chips", status_code=HTTP_201_CREATED,
             # responses={
             #     400: {"model": HTTPError, "description": "Invalid values or state"},
             #     403: {"model": HTTPError, "description": "No access for requested operation"},
             #     404: {"model": HTTPError, "description": "Club not found"},
             # },
             summary="Add chips in the club")
async def v1_add_club_chips(club_id: int, params: ChipsParams, users=Depends(check_rights_user_club_owner_or_manager)): #-> ChipsTxnItem:
    """
    Добавить определенное значение фишек на баланса клуба.

    Ожидаемое тело запроса:
    {
        "amount": number [значение amount не может быть <= 0]
    }

    Возвращает status code = 200
    """
    async with DBI() as db:
        club_owner_account, user, club = users

        await db.txn_with_chip_on_club_balance(club_id, params.amount, "CASHIN", club_owner_account.id, user.id)

        created_ts = DateTime.utcnow().replace(microsecond=0).timestamp()
        return HTTP_200_OK
    # return ChipsTxnItem(id=1,  #Todo
    #                     created_ts=created_ts,
    #                     created_by=user.id,
    #                     txn_type='CHIPSIN' if params.amount > 0 else 'CHIPSOUT',
    #                     amount=params.amount,
    #                     balance=params.amount,
    #                     ref_user_id=None,
    #                     ref_agent_id=None
    #                     )


@router.delete("/{club_id}/club/chips", status_code=HTTP_201_CREATED,
             # responses={
             #     400: {"model": HTTPError, "description": "Invalid values or state"},
             #     403: {"model": HTTPError, "description": "No access for requested operation"},
             #     404: {"model": HTTPError, "description": "Club not found"},
             # },
             summary="Remove chips in the club")
async def v1_remove_club_chips(club_id: int, params: ChipsParams, users=Depends(check_rights_user_club_owner_or_manager)): #-> ChipsTxnItem:
    """
    Удалить определенное значение фишек с баланса клуба.

    Ожидаемое тело запроса:
    {
        "amount": number [значение amount не может быть <= 0]
    }

    Возвращает status code = 200
    """
    async with DBI() as db:
        club_owner_account, user, club = users

        await db.txn_with_chip_on_club_balance(club_id, params.amount, "REMOVE", club_owner_account.id, user.id)

        created_ts = DateTime.utcnow().replace(microsecond=0).timestamp()
    return HTTP_200_OK
