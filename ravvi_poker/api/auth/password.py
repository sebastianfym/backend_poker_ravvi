from fastapi import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED

from .router import router
from .types import UserChangePassword
from ..utils import SessionUUID, get_session_and_user
from ...db import DBI
from ...engine.passwd import password_verify, password_hash


@router.post("/password")
async def v1_user_password(params: UserChangePassword, session_uuid: SessionUUID):
    """Change password"""
    if not params.new_password:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="New password required")
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        if user.password_hash:
            if not params.current_password:
                raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
            if not password_verify(params.current_password, user.password_hash):
                raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
        elif params.current_password:
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
        hash = password_hash(params.new_password)
        await db.update_user_password(user.id, password_hash=hash)
    return {}