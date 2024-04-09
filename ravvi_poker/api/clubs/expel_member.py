from logging import getLogger
from fastapi import Depends
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND

from .utilities import check_rights_user_club_owner_or_manager
from ..users.types import black_list_symbols
from ...db import DBI
from ..utils import SessionUUID, get_session_and_user, check_club_name
from .router import router
from .types import *

log = getLogger(__name__)


@router.post("/{club_id}/expel/{user_id}", summary="Выгнать пользователя из клуба",
             responses={
                 404: {"model": ErrorException, "detail": "Club not found",
                       "message": "Club not found"},
                 403: {"model": ErrorException, "detail": "Permission denied",
                       "message": "You dont have permission for this action"},
                 400: {"model": ErrorException, "detail": "Member has  agent",
                       "message": "Member has  agent"}
             })
async def v1_expel_member(club_id: int, user_id: int, session_uuid: SessionUUID) -> ClubMemberProfile:
    """
    Служит для исключение пользователя из клуба

    - **club_id**: number

    - **user_id**: number

    """
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")

        account = await db.find_account(user_id=user.id, club_id=club_id)
        member = await db.find_account(user_id=user_id, club_id=club_id)
        user_member = await db.get_user(id=user_id)

        if not account:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="You are not a member in this club")
        if account.user_role not in ["O", "M"]:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="You dont have permission for this action")

        if not member:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club member not found")
        elif member.agent_id is not None:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Member has  agent")
        elif member.user_role is "O":
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Member is owner")

        return_balance = member.balance + member.balance_shared

        await db.expel_member_from_club(member.id, club_id)

        await db.refresh_club_balance(club_id, return_balance, 'pick_up')

        return ClubMemberProfile(
            id=user_member.id,
            username=user_member.name,
            nickname=member.nickname,
            image_id=user_member.image_id,
            user_role=member.user_role,
            user_approved=member.approved_ts is not None,
            country=user_member.country,
            balance=0.0000,
            balance_shared=0.0000,
            join_in_club=member.created_ts.timestamp()
        )