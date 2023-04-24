from typing import Annotated, Optional

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from pydantic import BaseModel
from . import utils

from ..db.dbi import DBI

from .auth import get_current_session_uuid

router = APIRouter(prefix="/user", tags=["user"])

RequireSessionUUID = Annotated[str, Depends(get_current_session_uuid)]

class UserChangePassword(BaseModel):
    current_password: str | None = None
    new_password: str | None

@router.post("/password")
async def v1_user_password(params: UserChangePassword, session_uuid: RequireSessionUUID):
    if not params.new_password:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Bad password")
    with DBI() as dbi:
        session = dbi.get_session_by_uuid(session_uuid)
        if not session:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid session")
        user = dbi.get_user(id=session.user_id)
        if not user:
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid user")
        if params.current_password:
            if not user.password_hash or not utils.password_verify(params.current_password, user.password_hash):
                raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
        hash = utils.password_hash(params.new_password)
        dbi.update_user_password(user.id, password_hash=hash)
    return {}


@router.post("/logout")
async def v1_user_logout(session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        session = dbi.get_session_by_uuid(session_uuid)
        if not session:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid session")


@router.get("/profile")
async def v1_user_profile(session_uuid: RequireSessionUUID):
    return {"msg": "Hello World"}
