import json
import os
import re
from typing import Annotated
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND
from fastapi import Depends
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordBearer

from ..db import DBI
from ..engine.jwt import jwt_get

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login_form")

forbidden_words = ['fuck', 'shit', 'f*ck', 'f**k']

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
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid session")
    user = await db.get_user(id=session.user_id)
    if not user or user.closed_ts:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail="Invalid user")
    return session, user

async def get_club_and_member(db: DBI, club_id: int, user_id: int, roles_required: list[str]|None):
    club = await db.get_club(club_id)
    if not club:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND,
                            detail="Club not found")
    member = await db.find_member(club_id=club_id, user_id=user_id)
    if not member or member.approved_ts is None or member.closed_ts is not None:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN,
                            detail="You are not club member")
    if member.user_role not in roles_required:
        raise HTTPException(status_code=HTTP_403_FORBIDDEN,
                            detail="No access to function")
    return club, member


def get_country_code(country):
    for file_name in ['countries_ru', 'countries_en']:
        relative_path = f'engine/data/{file_name}.json'
        absolute_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', relative_path))

        with open(absolute_path, 'r') as countries_file:
            countries_dict = json.load(countries_file)
            if country in countries_dict.keys():
                return country
    raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail='Invalid country')


def check_username(name, user_id):
    if name.isdigit():
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Name should not consist only of digits")
    for bad_word in forbidden_words:
        if bad_word.lower() in name.lower():
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Name contains forbidden word")
    pattern = fr'^[uU]\d+$'
    match = re.match(pattern, name)
    if match:
        pattern = fr'^[uU]{user_id}$'
        match = re.match(pattern, name)
        if match is None:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid name")


def check_email(email):
    if email.isdigit():
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Email should not consist only of digits")
    for bad_word in forbidden_words:
        if bad_word.lower() in email.lower():
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Email contains forbidden word")

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    match = re.fullmatch(pattern, email)
    if match is None:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid email")


def check_club_name(name, club_id):
    if name.isdigit():
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Name should not consist only of digits")
    for bad_word in forbidden_words:
        if bad_word.lower() in name.lower():
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Name contains forbidden word")
    pattern = fr'^[Cc][Ll][Uu][Bb]-\d+$'
    match = re.match(pattern, name)

    if match:
        if int(name.split("-")[1]) != club_id:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid name")


def username_or_email(string):
    email_pattern = r'^[^@]+@[^@]+\.[^@]+$'

    if re.match(email_pattern, string):
        return True
    else:
        return False


