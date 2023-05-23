from typing import Annotated, Optional
from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.exceptions import HTTPException
from pydantic import BaseModel
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED

from . import utils
from ..db.dbi import DBI

router = APIRouter(prefix="/auth", tags=["auth"])


class DeviceInfo(BaseModel):
    device_token: str | None
    device_props: dict | None


class UserAccessTokens(BaseModel):
    device_token: str | None
    access_token: str | None
    token_type: str = "bearer"
    user_id: int | None
    username: str | None


@router.post("/register")
async def register_guest(params: DeviceInfo) -> UserAccessTokens:
    """Register user account (guest)"""

    device_uuid = utils.jwt_get(params.device_token, "device_uuid")

    with DBI() as dbi:
        user = dbi.create_user_account()
        device = dbi.get_device(uuid=device_uuid)
        if device is None:
            device = dbi.create_device(params.device_props)
        login = dbi.create_user_login(user.id, device.id)
        session = dbi.create_user_session(login.id)

        device_token = utils.jwt_encode(device_uuid=str(device.uuid), login_uuid=str(login.uuid))
        access_token = utils.jwt_encode(session_uuid=str(session.uuid))

    response = UserAccessTokens(
            device_token=device_token, 
            access_token=access_token,
            user_id=user.id, 
            username=user.username
        )
    return response


@router.post("/device")
async def v1_device_login(params: DeviceInfo) -> UserAccessTokens:
    """Login with device token"""
    device_uuid, login_uuid = utils.jwt_get(params.device_token, "device_uuid", "login_uuid")
    with DBI() as dbi:
        device = dbi.get_device(uuid=device_uuid)
        login  = dbi.get_user_login(uuid=login_uuid)
        user   = dbi.get_user(id=login.user_id)
        if device and login and user:
            # TODO: close any open session for login_id
            session = dbi.create_user_session(login.id)
            device_token = utils.jwt_encode(device_uuid=str(device.uuid), login_uuid=str(login.uuid))
            access_token = utils.jwt_encode(session_uuid=str(session.uuid))
            user_id = user.id
            username = user.username
        elif device:
            device_token = utils.jwt_encode(device_uuid=str(device.uuid))
            access_token = None
            user_id = None
            username = None

    response =  UserAccessTokens(
        device_token=device_token, 
        access_token=access_token, 
        user_id=user_id,
        username=username
        )
    return response
  

@router.post("/login", responses={400: {}, 401: {}})
async def v1_user_login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """Login with username / password"""
    device_token = form_data.client_id
    device_uuid, login_uuid = utils.jwt_get(device_token, "device_uuid", "login_uuid")

    if not form_data.username or not form_data.password:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Incorrect username or password")
    with DBI() as dbi:
        device = dbi.get_device(uuid=device_uuid)
        if not device:
            device = dbi.create_device({})
        if login_uuid:
            dbi.close_user_login(uuid=login_uuid)
        user = dbi.get_user(username=form_data.username)
        if not user or not form_data.password:
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
        if not utils.password_verify(form_data.password, user.password_hash):
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

        login = dbi.create_user_login(user.id, device.id)
        session = dbi.create_user_session(login.id)

        device_token = utils.jwt_encode(device_uuid=str(device.uuid), login_uuid=str(login.uuid))
        access_token = utils.jwt_encode(session_uuid=str(session.uuid))

    response = UserAccessTokens(
            device_token=device_token, 
            access_token=access_token,
            user_id=user.id, 
            username=user.username
        )
    return response


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")

async def get_current_session_uuid(access_token: Annotated[str, Depends(oauth2_scheme)]):
    session_uuid = utils.jwt_get(access_token, "session_uuid")
    if not session_uuid:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return session_uuid


RequireSessionUUID = Annotated[str, Depends(get_current_session_uuid)]


def get_session_and_user(dbi, session_uuid):
    session = dbi.get_session_info(uuid=session_uuid)
    if not session:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid session")
    user = dbi.get_user(id=session.user_id)
    if not user:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid user")
    return session, user


class UserChangePassword(BaseModel):
    current_password: str | None = None
    new_password: str | None


@router.post("/password")
async def v1_user_password(params: UserChangePassword, session_uuid: RequireSessionUUID):
    """Change password"""
    if not params.new_password:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Bad password")
    with DBI() as dbi:
        session = dbi.get_session_info(uuid=session_uuid)
        if not session:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid session")
        user = dbi.get_user(id=session.user_id)
        if not user:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid user")
        if params.current_password:
            if not user.password_hash or not utils.password_verify(params.current_password, user.password_hash):
                raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
        hash = utils.password_hash(params.new_password)
        dbi.update_user_password(user.id, password_hash=hash)
    return {}


@router.post("/logout")
async def v1_user_logout(session_uuid: RequireSessionUUID):
    """Logout"""    
    with DBI() as dbi:
        session = dbi.get_session_info(uuid=session_uuid)
        if session:
            dbi.close_user_session(session_id=session.session_id, login_id=session.login_id)
            device_token = utils.jwt_encode(device_uuid=str(session.device_uuid))
        else:
            device_token = None

    return UserAccessTokens(device_token=device_token)
