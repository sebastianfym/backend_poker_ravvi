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
                        users=Depends(check_rights_user_club_owner_or_manager)):# -> ChipsTxnItem:
    """
    Добавить или списать фишки с агентов

    {
        "mode": string, ["pick_up", "give_out"]
        "amount": number, [значение amount не может быть <= 0]
    }

    """
    async with DBI() as db:
        club_owner_account, user, club = users
        created_ts = DateTime.utcnow().replace(microsecond=0).timestamp()
        if params.mode == "give_out":
            await db.giving_chips_to_the_user(params.amount, user_id, "balance_shared", user.id)
        elif params.mode == "pick_up":
            await db.delete_chips_from_the_agent_balance(params.amount, user_id, club_owner_account.id)
        else:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Possible options: pick_up | give_out")
        return HTTP_200_OK
    # return ChipsTxnItem(id=1,
    #                     created_ts=created_ts,
    #                     created_by=user.id,
    #                     txn_type='MOVEIN' if params.amount > 0 else 'MOVEOUT',
    #                     amount=-params.amount,
    #                     balance=params.amount
    #                     )
