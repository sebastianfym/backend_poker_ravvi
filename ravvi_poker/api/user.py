import base64
import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter
from pydantic import BaseModel, EmailStr

from ..db.dbi import DBI
from .auth import RequireSessionUUID, get_session_and_user

BASE_PATH = Path(__file__).parent
USER_PHOTO_PATH = BASE_PATH.joinpath("user_photos")

router = APIRouter(prefix="/user", tags=["user"])


class UserProfile(BaseModel):
    id: int
    username: str
    email: EmailStr | None
    has_password: bool
    photo: str | None


class UserEmail(BaseModel):
    email: EmailStr


class UserUpdateFields(BaseModel):
    username: str | None
    photo: str | None


async def get_user_profile(user) -> UserProfile:
    photo = await return_base64_photo(user.photo) if user.photo else user.photo
    has_password = bool(user.password_hash)

    return UserProfile(
        id=user.id,
        username=user.username,
        email=user.email,
        has_password=has_password,
        photo=photo,
    )


@router.get("/profile")
async def v1_get_user_profile(session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)

    return await get_user_profile(user)


async def save_base64_photo(base64_photo: str,
                            upload_path: Path = USER_PHOTO_PATH) -> str:
    """Сохраняет base64 фотографии

    Возвращает сгенерированное название фото.
    """
    Path(upload_path).mkdir(parents=True, exist_ok=True)

    bytes_photo = base64.b64decode(base64_photo.encode())
    photo_name = str(uuid.uuid4())
    full_photo_path = upload_path.joinpath(photo_name)
    async with aiofiles.open(full_photo_path, "wb") as photo:
        await photo.write(bytes_photo)
    return photo_name


async def return_base64_photo(photo_name: str,
                              upload_path: Path = USER_PHOTO_PATH) -> str:
    """Возвращает фото в формате base64"""
    full_photo_path = upload_path.joinpath(photo_name)
    async with aiofiles.open(full_photo_path, "rb") as photo:
        base64_photo = base64.b64encode(await photo.read())
    return base64_photo


async def update_user_photo(user, base64_photo, upload_path=USER_PHOTO_PATH):
    if user.photo:
        full_old_photo_path = USER_PHOTO_PATH.joinpath(user.photo)
        full_old_photo_path.unlink(missing_ok=True)

    return await save_base64_photo(base64_photo)


@router.patch("/profile")
async def v1_update_user_profile(params: UserUpdateFields,
                                 session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)

        if params.photo:
            params.photo = await update_user_photo(user, params.photo)
        for field in UserUpdateFields.__fields__.keys():
            field_value = getattr(params, field, None)
            field_value = field_value if field_value else getattr(user, field)
            setattr(params, field, field_value)
        user = dbi.update_user_profile(user.id, params.username, params.photo)

    return await get_user_profile(user)


@router.delete("/profile", status_code=204)
async def v1_deactivate_user(session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        dbi.deactivate_user(user.id)

    return {}


@router.post("/profile/email")
async def v1_set_user_email(params: UserEmail, session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        user = dbi.update_user_email(user.id, params.email)

    return await get_user_profile(user)
