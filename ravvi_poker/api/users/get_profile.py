from .router import router
from .types import UserPrivateProfile
from ..utils import SessionUUID, get_session_and_user
from ...db import DBI


@router.get("/profile", summary="Get user private profile")
async def v1_get_user_private(session_uuid: SessionUUID):
    """Get user private profile"""
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)

    return UserPrivateProfile.from_row(user)