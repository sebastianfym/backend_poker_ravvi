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

log = getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterParams(BaseModel):
    device_token: str | None = None
    device_props: dict | None = None

class DeviceInfo(BaseModel):
    device_token: str | None = None
    login_token: str  | None = None
    device_props: dict | None = None


class UserAccessTokens(BaseModel):
    device_token: str | None = None
    login_token: str | None = None
    access_token: str | None = None
    token_type: str = "bearer"
    user_id: int | None = None
    username: str | None = None


@router.post("/register")
async def v1_register_guest(params: RegisterParams, request: Request) -> UserAccessTokens:
    """Register user account (guest)"""

    client_host = request.client.host
    device_uuid = jwt_get(params.device_token, "device_uuid")
    log.info("%s: auth.register device=%s", client_host, device_uuid)

    async with DBI() as db:
        user = await db.create_user()
        device = await db.get_device(uuid=device_uuid) if device_uuid else None
        if not device or device.closed_ts:
            device = await db.create_device(params.device_props)
        login = await db.create_login(device.id, user.id)
        session = await db.create_session(login.id)
        
    device_token = jwt_encode(device_uuid=str(device.uuid))
    login_token = jwt_encode(login_uuid=str(login.uuid))
    access_token = jwt_encode(session_uuid=str(session.uuid))

    response = UserAccessTokens(
            device_token=device_token, 
            login_token=login_token,
            access_token=access_token,
            user_id=user.id, 
            username=user.username or ""
        )
    return response


@router.post("/device")
async def v1_device_login(params: DeviceInfo, request: Request) -> UserAccessTokens:
    """Login with device/login token"""
    client_host = request.client.host
    device_uuid = jwt_get(params.device_token, "device_uuid")
    login_uuid = jwt_get(params.login_token, "login_uuid")
    log.info("%s: auth.device device=%s login=%s", client_host, device_uuid, login_uuid)

    async with DBI() as db:
        device = await db.get_device(uuid=device_uuid) if device_uuid else None
        login  = await db.get_login(uuid=login_uuid) if login_uuid else None
        user   = await db.get_user(id=login.user_id) if login and not login.closed_ts else None

        if user and user.closed_ts:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="User deactivated")
        
        if device and login and user:
            session = await db.create_session(login.id)
            device_token = jwt_encode(device_uuid=str(device.uuid))
            login_token = jwt_encode(login_uuid=str(login.uuid))
            access_token = jwt_encode(session_uuid=str(session.uuid))
            user_id = user.id
            username = user.username
        else:
            if not device:
                device = await db.create_device(params.device_props)
                device_token = jwt_encode(device_uuid=str(device.uuid))
            else:
                device_token = params.device_token
            login_token = None
            access_token = None
            user_id = None
            username = None

    response = UserAccessTokens(
        device_token=device_token, 
        login_token=login_token,
        access_token=access_token, 
        user_id=user_id,
        username=username
        )
    return response
  

@router.post("/login", responses={400: {}, 401: {}})
async def v1_login_form(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """Login with username / password"""
    device_uuid = jwt_get(form_data.client_id, "device_uuid") if form_data.client_id else None

    if not form_data.username or not form_data.password:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Missing username or password")
    try:
        user_id = int(form_data.username)
    except ValueError:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    
    async with DBI() as db:
        device = await db.get_device(uuid=device_uuid) if device_uuid else None
        if not device:
            device = await db.create_device()
            device_token = jwt_encode(device_uuid=str(device.uuid))
        #if login_uuid:
        #    dbi.close_user_login(uuid=login_uuid)
        user = await db.get_user(user_id)
        if not user:
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
        if user.closed_ts:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="User deactivated")
        if not password_verify(form_data.password, user.password_hash):
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
        login = await db.create_login(device.id, user.id)
        session = await db.create_session(login.id)

    device_token = jwt_encode(device_uuid=str(device.uuid))
    login_token = jwt_encode(login_uuid=str(login.uuid))
    access_token = jwt_encode(session_uuid=str(session.uuid))

    response = UserAccessTokens(
            device_token=device_token, 
            access_token=access_token,
            login_token=login_token,
            user_id=user.id, 
            username=user.username
        )
    return response



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
async def v1_user_logout(session_uuid: SessionUUID):
    """Logout"""    
    async with DBI() as db:
        session = await db.get_session_info(uuid=session_uuid) if session_uuid else None
        if session:
            await db.close_session(session.session_id)
            await db.close_login(session.login_id)
    return {}
