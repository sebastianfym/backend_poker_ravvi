from fastapi import HTTPException
from starlette.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_404_NOT_FOUND, HTTP_403_FORBIDDEN

from ...db import DBI
from ..utils import SessionUUID, get_session_and_user
from .types import ErrorException, ChipsActionParams, ChipsTxnInfo

from .router import router


@router.post(
    "/{club_id}/chips",
    status_code=HTTP_201_CREATED,
    responses={
        HTTP_400_BAD_REQUEST: {"model": ErrorException, "description": "Invalid request params"},
        HTTP_403_FORBIDDEN: {"model": ErrorException, "description": "No permission"},
        HTTP_404_NOT_FOUND: {"model": ErrorException, "description": "Club not found"},
    },
    summary="Добавить или списать фишки с баланса клуба",
)
async def v1_chips_club(club_id: int, params: ChipsActionParams, session_uuid: SessionUUID) -> ChipsTxnInfo:
    """
    Добавить или списать определенное значение фишек на баланса клуба.

    - **action**: IN|OUT - добвление/списание
    - **amount**: number > 0
    """

    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        operator = await db.find_member(club_id=club_id, user_id=user.id)
        if not operator or operator.approved_ts is None or operator.closed_ts is not None:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="You are not club member")
        if operator.user_role not in ["O", "M"]:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="No access to function")
        try:
            if params.action == "IN":
                txn_id = await db.create_txn_CHIPSIN(
                    txn_user_id=operator.user_id, club_id=club.id, txn_value=params.amount
                )
            elif params.action == "OUT":
                txn_id = await db.create_txn_CHIPSOUT(
                    txn_user_id=operator.user_id, club_id=club.id, txn_value=params.amount
                )
            else:
                raise HTTPException(HTTP_400_BAD_REQUEST, detail="Unexpected action")
        except db.Error as e:
            raise HTTPException(HTTP_400_BAD_REQUEST, detail="Logic error")

    return ChipsTxnInfo(txn_id=txn_id)
