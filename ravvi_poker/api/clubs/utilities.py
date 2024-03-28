from fastapi import HTTPException
from starlette.status import HTTP_403_FORBIDDEN, HTTP_400_BAD_REQUEST

from ravvi_poker.api.clubs.types import UserChipsValue
from ravvi_poker.api.utils import SessionUUID, get_session_and_user
from ravvi_poker.db import DBI


async def check_rights_user_club_owner(club_id: int, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN,
                                detail="You don't have enough rights to perform this action")
        elif club.closed_ts:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN,
                                detail="You don't have enough rights to perform this action")
        club_owner_account = await db.find_account(user_id=user.id, club_id=club_id)
        if club_owner_account is None or club_owner_account.user_role != "O":
            raise HTTPException(status_code=HTTP_403_FORBIDDEN,
                                detail="You don't have enough rights to perform this action")

    return club_owner_account, user, club


async def check_rights_user_club_owner_or_manager(club_id: int, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN,
                                detail="You don't have enough rights to perform this action")
        elif club.closed_ts:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN,
                                detail="You don't have enough rights to perform this action")
        club_owner_account = await db.find_account(user_id=user.id, club_id=club_id)
        if club_owner_account is None or club_owner_account.user_role.lower() not in ['o', 'm']:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN,
                                detail="You don't have enough rights to perform this action.")
        return club_owner_account, user, club


async def check_compatibility_recipient_and_balance_type(club_id: int, params: UserChipsValue):
    async with DBI() as db:
        club_member = await db.find_account(user_id=params.account_id, club_id=club_id)
    try:
        if club_member.user_role not in ["A", "S"] and params.balance == "balance_shared":
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='User has not agent balance')
        params.club_member = club_member
        return params
    except AttributeError:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='User account not found in club')