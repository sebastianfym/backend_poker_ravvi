from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, EmailStr
from starlette.status import HTTP_404_NOT_FOUND

from ..db.dbi import DBI
from .auth import RequireSessionUUID, get_session_and_user

router = APIRouter(prefix="/user", tags=["user"])


class UserProfile(BaseModel):
    id: int
    has_password: bool
    username: str | None = None
    email: EmailStr | None = None
    image_id: int | None = None


class UserProfileInfo(BaseModel):
    id: int
    username: str | None = None
    image_id: int | None = None


class UserProps(BaseModel):
    username: str | None = None
    image_id: int | None = None


class UserEmail(BaseModel):
    email: EmailStr


@router.get("/profile", summary="Get user")
async def v1_get_user(session_uuid: RequireSessionUUID):
    """Get user"""
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)

    return UserProfile(
        id=user.id,
        username=user.username,
        email=user.email,
        has_password=bool(user.password_hash),
        image_id=user.image_id
    )


@router.delete("/profile", status_code=204, summary="Deactivate user")
async def v1_deactivate_user(session_uuid: RequireSessionUUID):
    """Deactivate user"""
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        dbi.deactivate_user(user.id)

    return {}


@router.patch("/profile", summary="Update user")
async def v1_update_user(params: UserProps, session_uuid: RequireSessionUUID):
    """Update user"""
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        user_params = params.model_dump(exclude_unset=True)
        if user_params:
            image_id = user_params.get("image_id")
            image = dbi.get_user_images(user.id, id=image_id) if image_id else None
            if image_id and not image:
                raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Image not found")
            user = dbi.update_user_profile(user.id, **user_params)

    return UserProfile(
        id=user.id,
        username=user.username,
        email=user.email,
        has_password=bool(user.password_hash),
        image_id=user.image_id
    )


@router.post("/profile/email", summary="Set user email")
async def v1_set_user_email(params: UserEmail, session_uuid: RequireSessionUUID):
    """Set user email"""
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        user = dbi.update_user_profile(user.id, **params.model_dump())

    return UserProfile(
        id=user.id,
        username=user.username,
        email=user.email,
        has_password=bool(user.password_hash),
        image_id=user.image_id
    )


@router.get("/{user_id}/profile", summary="Get user info")
async def v1_get_user_profile(user_id: int, session_uuid: RequireSessionUUID):
    """Get user profile info"""
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        searched_user = dbi.get_user(id=user_id)
        if not searched_user:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="User not found")

    return UserProfileInfo(
        id=searched_user.id,
        username=searched_user.username,
        image_id=searched_user.image_id
    )
