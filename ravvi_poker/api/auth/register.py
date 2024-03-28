from logging import getLogger
from fastapi import APIRouter, Request, Depends

from .router import router
from .types import UserAccessProfile
from ..users.types import DeviceProps, UserPrivateProfile
# from ..types import DeviceProps, UserPrivateProfile
from ...db import DBI
from ...engine.jwt import jwt_get, jwt_encode

log = getLogger(__name__)

@router.post("/register")
async def v1_register(params: DeviceProps, request: Request) -> UserAccessProfile:
    """Register user account (guest)"""
    try:
        client_host = request.client.host
    except AttributeError:
        client_host = "127.0.0.1"
    device_uuid = jwt_get(params.device_token, "device_uuid")
    log.info("%s: auth.register device=%s", client_host, device_uuid)

    async with DBI() as db:
        user = await db.create_user()
        device = await db.get_device(uuid=device_uuid) if device_uuid else None
        if not device or device.closed_ts:
            device = await db.create_device(params.device_props)
        login = await db.create_login(device.id, user.id, host=client_host)
        session = await db.create_session(login.id, client_host)

    device_token = jwt_encode(device_uuid=str(device.uuid))
    login_token = jwt_encode(login_uuid=str(login.uuid))
    access_token = jwt_encode(session_uuid=str(session.uuid))

    response = UserAccessProfile(
        device_token=device_token,
        login_token=login_token,
        access_token=access_token,
        user=UserPrivateProfile.from_row(user)
    )
    return response