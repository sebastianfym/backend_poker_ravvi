from logging import getLogger
from fastapi import APIRouter, Request, Depends

from fastapi import HTTPException
from starlette.status import HTTP_403_FORBIDDEN

from .router import router
from .types import UserAccessProfile
from ..users.types import DeviceLoginProps, UserPrivateProfile
# from .types import DeviceLoginProps, UserPrivateProfile
from ...db import DBI
from ...engine.jwt import jwt_get, jwt_encode

log = getLogger(__name__)

@router.post("/device")
async def v1_device(params: DeviceLoginProps, request: Request) -> UserAccessProfile:
    """Login with device/login token"""
    # TODO: ip detection POKER-616
    try:
        client_host = request.client.host
    except AttributeError:
        client_host = "127.0.0.1"
    device_uuid = jwt_get(params.device_token, "device_uuid")
    login_uuid = jwt_get(params.login_token, "login_uuid")
    log.info("%s: auth.device device=%s login=%s", client_host, device_uuid, login_uuid)

    async with DBI() as db:
        device = await db.get_device(uuid=device_uuid) if device_uuid else None
        # find login only if device found
        login = await db.get_login(uuid=login_uuid) if device and login_uuid else None
        # find user only if login is valid
        user = await db.get_user(id=login.user_id) if login and not login.closed_ts else None

        if user and user.closed_ts:
            # check user closed
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="User deactivated")

        if not device:
            device = await db.create_device(params.device_props)
            device_token = jwt_encode(device_uuid=str(device.uuid))
            login_token = None
            access_token = None
        elif login and user:
            session = await db.create_session(login.id, client_host)
            device_token = jwt_encode(device_uuid=str(device.uuid))
            login_token = jwt_encode(login_uuid=str(login.uuid))
            access_token = jwt_encode(session_uuid=str(session.uuid))
        else:
            device_token = params.device_token
            login_token = None
            access_token = None

    response = UserAccessProfile(
        device_token=device_token,
        login_token=login_token,
        access_token=access_token,
        user=UserPrivateProfile.from_row(user) if user else None
    )
    return response