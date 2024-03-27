import re

from fastapi import HTTPException, Request
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from .types import UserAccessProfile
from ravvi_poker.api.users.types import UserPrivateProfile
# from ravvi_poker.api.types import UserPrivateProfile
from ravvi_poker.db import DBI
from ravvi_poker.engine.jwt import jwt_encode
from ravvi_poker.engine.passwd import password_verify


def username_or_email(string):
    email_pattern = r'^[^@]+@[^@]+\.[^@]+$'

    if re.match(email_pattern, string):
        return True
    else:
        return False


async def handle_login(device_uuid, request: Request, username=None, password=None):
    async with DBI() as db:
        device = await db.get_device(uuid=device_uuid) if device_uuid else None
        if not device:
            device = await db.create_device()
            device_token = jwt_encode(device_uuid=str(device.uuid))
        # if login_uuid:
        #    dbi.close_user_login(uuid=login_uuid)
        if username.isdigit():
            user_id = int(username)
            user = await db.get_user(user_id)
        elif username_or_email(username):
            user = await db.get_user_by_email(username)
        else:
            user = await db.get_user_by_name(username)

        if not user:
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
        if user.closed_ts:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="User deactivated")
        if not password_verify(password, user.password_hash):
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

        try:
            client_host = request.client.host
        except AttributeError:
            client_host = "127.0.0.1"

        login = await db.create_login(device.id, user.id, host=client_host)
        session = await db.create_session(login.id, client_host)

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
