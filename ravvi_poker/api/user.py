from fastapi import APIRouter
from pydantic import BaseModel, EmailStr

from ..db.dbi import DBI
from .auth import RequireSessionUUID, get_session_and_user

router = APIRouter(prefix="/user", tags=["user"])


class UserProfile(BaseModel):
    id: int
    username: str
    email: EmailStr | None
    has_password: bool


class UserEmail(BaseModel):
    email: EmailStr


class UserUpdateFields(BaseModel):
    username: str


@router.get("/profile")
async def v1_get_user_profile(session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)

    return UserProfile(
        id=user.id,
        username=user.username,
        email=user.email,
        has_password=bool(user.password_hash)
    )


@router.put("/profile")
async def v1_update_user_profile(params: UserUpdateFields, session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        user = dbi.update_user(user.id, params.username)

    return UserProfile(
        id=user.id,
        username=user.username,
        email=user.email,
        has_password=bool(user.password_hash)
    )


@router.post("/profile/email")
async def v1_set_user_email(params: UserEmail, session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        user = dbi.update_user_email(user.id, params.email)

    return UserProfile(
        id=user.id,
        username=user.username,
        email=user.email,
        has_password=bool(user.password_hash)
    )
