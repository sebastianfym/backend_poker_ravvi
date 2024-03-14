from fastapi import HTTPException
from starlette.status import HTTP_403_FORBIDDEN

from ravvi_poker.api.utils import get_session_and_user, SessionUUID
from ravvi_poker.db import DBI


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