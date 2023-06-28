from typing import Annotated, Optional

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED
from pydantic import BaseModel, EmailStr
from . import utils

from ..db.dbi import DBI
from .auth import RequireSessionUUID

router = APIRouter(prefix="/user", tags=["user"])


class UserProfile(BaseModel):
    id: int
    username: str
    email: EmailStr | None
    has_password: bool


class UserProfileEmail(BaseModel):
    email: EmailStr


@router.get("/profile")
async def v1_user_profile(session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        session = dbi.get_session_info(uuid=session_uuid)
        if not session:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid session")
        user = dbi.get_user(id=session.user_id)
        if not user:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid user")

    return UserProfile(id=user.id, username=user.username, email=user.email, has_password=bool(user.password_hash))


@router.post("/profile/email")
async def v1_profile_email(params: UserProfileEmail, session_uuid: RequireSessionUUID):
    if not params.email:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Bad email")
    with DBI() as dbi:
        session = dbi.get_session_info(uuid=session_uuid)
        if not session:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid session")
        user = dbi.get_user(id=session.user_id)
        if not user:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid user")
        dbi.update_user_email(user.id, params.email)

    return UserProfile(id=user.id, username=user.username, email=user.email, has_password=bool(user.password_hash))
