import json
import os

from fastapi import HTTPException
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST

from .router import *
from ..utils import SessionUUID, get_session_and_user
from ...db import DBI


@router.get("/countries/{language}", status_code=HTTP_200_OK, summary="Get a list of countries in different languages")
async def v1_get_countries(session_uuid: SessionUUID, language: str):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
    match language:
        case "ru":
            file_name = 'countries_ru'
        case "en":
            file_name = 'countries_en'
        case _:
            file_name = 'countries_en'

    try:
        relative_path = f'../engine/data/{file_name}.json'
        absolute_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', relative_path))

        with open(absolute_path, 'r') as countries_file:
            countries_dict = json.load(countries_file)
            return countries_dict
    except Exception as exception:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=exception)