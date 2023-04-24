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
    access_token: str
    token_type: str = "bearer"
    username: str

@router.post("/register")
async def register(params: DeviceInfo) -> UserAccessTokens: 
    """Register user account (guest)"""

    device_uuid = utils.jwt_get(params.device_token, 'device_uuid')

    with DBI() as dbi:
        user = dbi.create_user_account()
        device = dbi.get_device(uuid=device_uuid)
        if device is None:
            device = dbi.create_device(params.device_props)
        login = dbi.create_user_login(user.id, device.id)
        session = dbi.create_user_session(login.id)
    
        device_token = utils.jwt_encode(device_uuid=str(device.uuid), login_uuid=str(login.uuid))
        access_token = utils.jwt_encode(session_uuid=str(session.uuid))

    return UserAccessTokens(
        device_token = device_token,
        access_token = access_token,
        username = user.username
    )


@router.post("/login", responses={400: {}, 401: {}})
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    device_token = form_data.client_id
    device_uuid, login_uuid = utils.jwt_get(device_token, 'device_uuid', 'login_uuid')

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

    return UserAccessTokens(
        device_token = device_token,
        access_token = access_token,
        username = user.username
    )


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")
async def get_current_session_uuid(access_token: Annotated[str, Depends(oauth2_scheme)]):
    session_uuid = utils.jwt_get(access_token, 'session_uuid')
    if not session_uuid:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return session_uuid
