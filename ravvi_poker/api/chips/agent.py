from fastapi import HTTPException
from starlette.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND

from ...db import DBI
from ..utils import SessionUUID, get_session_and_user
from .types import ErrorException, ChipsActionParams, ChipsTxnInfo

from .router import router


@router.post(
    "/{club_id}/chips/agents/{agent_user_id}",
    status_code=HTTP_201_CREATED,
    responses={
        HTTP_400_BAD_REQUEST: {"model": ErrorException, "description": "Invalid request params"},
        HTTP_403_FORBIDDEN: {"model": ErrorException, "description": "No permission"},
        HTTP_404_NOT_FOUND: {"model": ErrorException, "description": "Club not found"},
    },
    summary="Добавить или списать фишки с баланса агента",
)
async def v1_chips_agent(
    club_id: int, agent_user_id: int, params: ChipsActionParams, session_uuid: SessionUUID
) -> ChipsTxnInfo:
    """
    Добавить или забрать фишки с баланса агента.

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
        if operator.user_role not in ["O", "M", "S"]:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="No access to function")
        ref_member_id = operator.id if operator.user_role == "S" else None

        agent = await db.find_member(club_id=club_id, user_id=agent_user_id)
        if not agent or agent.approved_ts is None:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Agent not found")
        try:
            if params.action == "IN":
                txn_id = await db.create_txn_MOVEIN(
                    txn_user_id=operator.user_id,
                    club_id=club.id,
                    member_id=agent.id,
                    txn_value=params.amount,
                    ref_member_id=ref_member_id,
                )
            elif params.action == "OUT":
                txn_id = await db.create_txn_MOVEOUT(
                    txn_user_id=operator.user_id,
                    club_id=club.id,
                    member_id=agent.id,
                    txn_value=params.amount,
                    ref_member_id=ref_member_id,
                )
            else:
                raise HTTPException(HTTP_400_BAD_REQUEST, detail="Unexpected action")
        except db.Error as e:
            raise HTTPException(HTTP_400_BAD_REQUEST, detail="TODO: error")

    return ChipsTxnInfo(txn_id=txn_id)
