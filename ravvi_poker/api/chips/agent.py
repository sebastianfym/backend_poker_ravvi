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
from .types import ChipsParams, ChipsTxnItem, ChipsParamsForAgents, ErrorException
from .router import router


@router.post("/{club_id}/agents/chips/{user_id}", status_code=HTTP_201_CREATED,
             responses={
                 400: {"model": ErrorException, "detail": "Invalid mode values", "message": "Possible options: pick_up | give_out"}
             },
             summary="Добавить или списать фишки с агентов")
async def v1_club_chips(club_id: int, user_id: int, params: ChipsParamsForAgents,
                        users=Depends(check_rights_user_club_owner_or_manager)) -> ChipsTxnItem:
    """
    Добавить или списать фишки с агентов

    - **mode**: "pick_up" | "give_out"
    - **amount**: number >= 1
    """
    async with DBI() as db:
        club_owner_account, user, club = users
        created_ts = DateTime.utcnow().replace(microsecond=0).timestamp()
        if params.mode == "give_out":
            row = await db.giving_chips_to_the_user(params.amount, user_id, "balance_shared", user.id)
            txn_model = ChipsTxnItem(
                id=row.id,
                created_ts=created_ts,
                created_by=row.sender_id,
                # txn_type='MOVEIN' if params.amount > 0 else 'MOVEOUT',
                txn_type=row.txn_type,
                amount=row.txn_value,
                balance=row.total_balance
            )
        elif params.mode == "pick_up":
            row = await db.delete_chips_from_the_agent_balance(params.amount, user_id, club_owner_account.id)
            txn_model = ChipsTxnItem(
                    id=row[1].id,
                    created_ts=created_ts,
                    created_by=row[1].sender_id,
                    # txn_type='MOVEIN' if params.amount > 0 else 'MOVEOUT',
                    txn_type=row[1].txn_type,
                    amount=row[1].txn_value,
                    balance=row[1].total_balance
                )
        else:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Possible options: pick_up | give_out")
        return txn_model
    # return ChipsTxnItem(id=1,
    #                     created_ts=created_ts,
    #                     created_by=user.id,
    #                     txn_type='MOVEIN' if params.amount > 0 else 'MOVEOUT',
    #                     amount=-params.amount,
    #                     balance=params.amount
    #                     )
