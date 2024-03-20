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
from .types import ChipsParams, ChipsTxnItem, ErrorException

from .router import router


@router.post("/{club_id}/club/chips", status_code=HTTP_201_CREATED,
             responses={
                 400: {"model": ErrorException, "description": "Possible amount must be more or less 0"},
                 403: {"model": ErrorException, "description": "You dont have permissions"},
                 404: {"model": ErrorException, "description": "Club not found"},
             },
             summary="Добавить или списать фишки с баланса клуба")
async def v1_add_club_chips(club_id: int, params: ChipsParams, session_uuid: SessionUUID) -> ChipsTxnItem:
    """
    Добавить или списать определенное значение фишек на баланса клуба.

    - **amount**: number >  0 | number < 0

    Если  число положительное, то произойдет  пополнение баланса, если отрицательное, то произойдет списание
    """

    async with DBI() as db:
        club_owner_account, user, club = await check_rights_user_club_owner_or_manager(club_id, session_uuid)
        if params.amount > 0:
            row = await db.txn_with_chip_on_club_balance(club_id, params.amount, "CHIPSIN", club_owner_account.id, user.id)
        elif params.amount < 0:
            row = await db.txn_with_chip_on_club_balance(club_id, params.amount, "CHIPSOUT", club_owner_account.id,user.id)
        else:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Possible amount must be more or less 0")
        created_ts = DateTime.utcnow().replace(microsecond=0).timestamp()
    return ChipsTxnItem(id=row.id,  #Todo
                        created_ts=created_ts,
                        created_by=user.id,
                        txn_type=row.txn_type,
                        amount=params.amount,
                        balance=row.total_balance,
                        ref_user_id=user.id,
                        ref_agent_id=None
                        )
