from starlette.status import HTTP_400_BAD_REQUEST

from .router import router
from .types import UserMutableProps, UserPrivateProfile, black_list_symbols
from ..utils import SessionUUID, get_session_and_user, get_country_code, check_username, check_email
from fastapi import Request, HTTPException

from ...db import DBI


@router.patch("/profile", summary="Update user profile")
async def v1_update_user(props: UserMutableProps, session_uuid: SessionUUID, request: Request):
    """Update user profile"""
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        kwargs = props.model_dump(exclude_unset=True)
        if "country" in kwargs.keys():
            kwargs['country'] = get_country_code(kwargs['country'])
        if "name" in kwargs.keys():
            name = kwargs['name']
            for symbol in black_list_symbols:
                if symbol in name:
                    raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="You are using forbidden characters")
            if await db.check_uniq_username(name, user.id) is not None:
                raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="This name is already taken")
            check_username(name, user.id)
        if "email" in kwargs.keys():
            email = kwargs['email']
            if await db.check_uniq_email(email) is not None:
                raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="This email is already taken")
            check_email(email)
        if "image_id" in kwargs.keys():
            image_id = kwargs["image_id"]
            if await db.check_img_id(image_id) is None:
                raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="This image not found")
        user = await db.update_user(user.id, **kwargs)
    return UserPrivateProfile.from_row(user)
