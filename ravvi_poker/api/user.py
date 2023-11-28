import logging
from uuid import UUID

from fastapi import APIRouter, Request
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, EmailStr
from starlette.status import HTTP_404_NOT_FOUND, HTTP_422_UNPROCESSABLE_ENTITY

from ..db import DBI as DBI
from .utils import SessionUUID, get_session_and_user

log = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["user"])


class UserPrivateProfile(BaseModel):
    id: int
    has_password: bool
    username: str | None = None
    email: EmailStr | None = None
    image_id: int | None = None


class UserPublicInfo(BaseModel):
    id: int
    username: str | None = None
    image_id: int | None = None


class UserProps(BaseModel):
    username: str | None = None
    image_id: int | None = None


class UserEmail(BaseModel):
    email: EmailStr


class UserTempEmail(BaseModel):
    user_id: int
    uuid: UUID
    temp_email: str
    is_active: bool


@router.get("/profile", summary="Get user private profile")
async def v1_get_user_profile(session_uuid: SessionUUID):
    """Get user private profile"""
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)

    return UserPrivateProfile(
        id=user.id,
        username=user.username,
        email=user.email,
        has_password=bool(user.password_hash),
        image_id=user.image_id
    )

@router.patch("/profile", summary="Update user profile")
async def v1_update_user(props: UserProps, session_uuid: SessionUUID, request: Request):
    """Update user profile"""
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        kwargs = props.model_dump(exclude_unset=True)
        if kwargs:
            user = await db.update_user(user.id, **kwargs)

    return UserPrivateProfile(
        id=user.id,
        username=user.username,
        email=user.email,
        has_password=bool(user.password_hash),
        image_id=user.image_id
    )

@router.get("/{user_id}", summary="Get user public info")
async def v1_get_user_info(user_id: int, session_uuid: SessionUUID):
    """Get user public info"""
    async with DBI() as db:
        await get_session_and_user(db, session_uuid)
        user = await db.get_user(user_id)
        if not user:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="User not found")

    return UserPublicInfo(
        id=user.id,
        username=user.username,
        image_id=user.image_id
    )
