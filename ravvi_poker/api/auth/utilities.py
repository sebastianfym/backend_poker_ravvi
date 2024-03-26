from fastapi import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from .types import UserAccessProfile
from ravvi_poker.api.users.types import UserPrivateProfile
# from ravvi_poker.api.types import UserPrivateProfile
from ravvi_poker.db import DBI
from ravvi_poker.engine.jwt import jwt_encode
from ravvi_poker.engine.passwd import password_verify


async def handle_login(device_uuid, username=None, password=None, id=None, email=None):
    async with DBI() as db:
        device = await db.get_device(uuid=device_uuid) if device_uuid else None
        if not device:
            device = await db.create_device()
            device_token = jwt_encode(device_uuid=str(device.uuid))
        #if login_uuid:
        #    dbi.close_user_login(uuid=login_uuid)
        if id:
            user_id = int(id)
            user = await db.get_user(user_id)
        elif username:
            user = await db.get_user_by_name(username)
        elif email:
            user = await db.get_user_by_email(email)
        else:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Missing username or password")

        if not user:
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
        if user.closed_ts:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="User deactivated")
        if not password_verify(password, user.password_hash):
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
        login = await db.create_login(device.id, user.id)
        session = await db.create_session(login.id)

    device_token = jwt_encode(device_uuid=str(device.uuid))
    login_token = jwt_encode(login_uuid=str(login.uuid))
    access_token = jwt_encode(session_uuid=str(session.uuid))

    response = UserAccessProfile(
            device_token=device_token,
            access_token=access_token,
            login_token=login_token,
            user=UserPrivateProfile.from_row(user)
        )
    return response
