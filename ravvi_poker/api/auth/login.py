from typing import Annotated
from fastapi import Request, Depends
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm

from .router import router
from .utilities import handle_login
from ..users.types import UserLoginProps
from ...engine.jwt import jwt_get


@router.post("/login", responses={400: {}, 401: {}, 403: {}})
async def v1_login(params: UserLoginProps, request: Request):
    """Login API with username / password"""
    device_uuid = jwt_get(params.device_token, "device_uuid")
    if params.username:
        return await handle_login(device_uuid=device_uuid, username=params.username, password=params.password)
    elif params.id:
        return await handle_login(device_uuid=device_uuid, id=params.id, password=params.password)
    elif params.email:
        return await handle_login(device_uuid=device_uuid, email=params.email, password=params.password)


@router.post("/login_form", responses={400: {}, 401: {}, 403: {}})
async def v1_login_form(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """Login Form with username / password"""
    device_uuid = jwt_get(form_data.client_id, "device_uuid") if form_data.client_id else None
    return await handle_login(device_uuid, username=form_data.username, password=form_data.password)