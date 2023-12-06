from typing import Annotated
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN
from fastapi import Depends
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer

from ..engine.jwt import jwt_get

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login_form")

async def get_current_session_uuid(access_token: Annotated[str, Depends(oauth2_scheme)]):
    session_uuid = jwt_get(access_token, "session_uuid")
    if not session_uuid:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return session_uuid

SessionUUID = Annotated[str, Depends(get_current_session_uuid)]

async def get_session_and_user(db, session_uuid):
    session = await db.get_session_info(uuid=session_uuid)
    if not session or session.session_closed_ts or session.login_closed_ts:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid session")
    user = await db.get_user(id=session.user_id)
    if not user or user.closed_ts:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid user")
    return session, user

