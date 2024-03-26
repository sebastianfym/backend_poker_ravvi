from logging import getLogger
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from ..engine.jwt import jwt_get, jwt_encode
from ..engine.passwd import password_hash, password_verify
from ..db import DBI

from .utils import SessionUUID, get_session_and_user
from .types import UserPrivateProfile, DeviceProps, DeviceLoginProps, UserLoginProps

log = getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


class UserAccessProfile(BaseModel):
    device_token: str | None = None
    login_token: str | None = None
    access_token: str | None = None
    token_type: str = "bearer"
    user: UserPrivateProfile|None


@router.post("/register")
async def v1_register(params: DeviceProps, request: Request) -> UserAccessProfile:
    """Register user account (guest)"""
    # TODO: ip detection POKER-616
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


async def handle_login(device_uuid, request: Request, username=None, password=None, id=None, email=None):
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


@router.post("/login", responses={400: {}, 401: {}, 403: {}})
async def v1_login(params: UserLoginProps, request: Request):
    """Login API with username / password"""
    device_uuid = jwt_get(params.device_token, "device_uuid")
    if params.username:
        return await handle_login(device_uuid=device_uuid, username=params.username, password=params.password, request=request)
    elif params.id:
        return await handle_login(device_uuid=device_uuid, id=params.id, password=params.password, request=request)
    elif params.email:
        return await handle_login(device_uuid=device_uuid, email=params.email, password=params.password, request=request)


@router.post("/login_form", responses={400: {}, 401: {}, 403: {}})
async def v1_login_form(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], request: Request):
    """Login Form with username / password"""
    device_uuid = jwt_get(form_data.client_id, "device_uuid") if form_data.client_id else None
    return await handle_login(device_uuid, username=form_data.username, password=form_data.password, request=request)


class UserChangePassword(BaseModel):
    current_password: str | None = None
    new_password: str | None = None


@router.post("/password")
async def v1_user_password(params: UserChangePassword, session_uuid: SessionUUID):
    """Change password"""
    if not params.new_password:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="New password required")
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        if user.password_hash:
            if not params.current_password:
                raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
            if not password_verify(params.current_password, user.password_hash):
                raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
        elif params.current_password:
                raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
        hash = password_hash(params.new_password)
        await db.update_user_password(user.id, password_hash=hash)
    return {}


@router.post("/logout")
async def v1_user_logout(session_uuid: SessionUUID, request: Request):
    """Logout"""    
    async with DBI() as db:
        session = await db.get_session_info(uuid=session_uuid) if session_uuid else None
        if session:
            try:
                client_host = request.client.host
            except AttributeError:
                client_host = "127.0.0.1"
            await db.close_session(session.session_id, host=client_host)
            await db.close_login(session.login_id, host=client_host)
    return {}
