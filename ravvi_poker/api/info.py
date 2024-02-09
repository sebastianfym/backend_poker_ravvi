import json
import os
from pathlib import Path

import pytz
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST

from ..db import DBI
from ..engine.info import levels_schedule, rewards_distribution
from ..engine.tables import TablesManager

from .utils import SessionUUID, get_session_and_user

manager = TablesManager()

router = APIRouter(prefix="/info", tags=["info"])

class TimeZoneInput(BaseModel):
    timezone_user: str | None


@router.get("/levels_schedule/{table_type}", status_code=HTTP_200_OK, summary="Get blind levels schedule (SNG/MTT)")
async def v1_get_all_info_about_blinds(table_type: str, session_uuid: SessionUUID):
    """
    Возвращает список уровнией для турниров.

    table_type - тип стола: SNG | MTT.
    """

    table_type = table_type.lower()

    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
    try:
        return levels_schedule[table_type]
    except KeyError:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Key not found")
    

@router.get("/rewards_distribution", status_code=HTTP_200_OK, summary="Get rewards distribution structure")
async def v1_get_payment_structure(session_uuid: SessionUUID):
    """
    Получаем структуру распределения выигрыша в турнирах.
    """
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)

    return rewards_distribution


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
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid language code")

    try:

        relative_path = f'engine/data/{file_name}.json'
        absolute_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', relative_path))

        with open(absolute_path, 'r') as countries_file:
            countries_dict = json.load(countries_file)
            return countries_dict
    except Exception as exception:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=exception)


@router.get("/timezone", status_code=HTTP_200_OK, summary="Get a list of countries in different languages")
async def v1_get_timezone_list(session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)

        timezone_list = pytz.all_timezones
        return timezone_list


@router.post("/timezone", status_code=HTTP_200_OK, summary="")
async def v1_set_timezone_list(params:  TimeZoneInput, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        timezone_user = params.timezone_user
        try:
            tz_object = pytz.timezone(timezone_user)
        except:
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid timezone")

        utc_offset_seconds = tz_object.utcoffset(pytz.datetime.datetime.now()).total_seconds()

        hours = int(utc_offset_seconds // 3600)
        minutes = int((utc_offset_seconds % 3600) // 60)

        offset_string = f"{hours}:{minutes}"

        return offset_string

