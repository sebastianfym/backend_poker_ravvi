from fastapi import HTTPException
from starlette.status import HTTP_404_NOT_FOUND

from .router import router
from .types import UserPublicProfile
from ..utils import SessionUUID, get_session_and_user
from ...db import DBI


@router.get("/{user_id}", summary="Get user public info")
async def v1_get_user_public(user_id: int, session_uuid: SessionUUID):
    """Get user public info"""
    async with DBI() as db:
        await get_session_and_user(db, session_uuid)
        user = await db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="User not found")

    return UserPublicProfile.from_row(user)