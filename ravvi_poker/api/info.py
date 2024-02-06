import datetime
import json
import os
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic.v1 import BaseModel
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_400_BAD_REQUEST

from ..db import DBI
from ..engine.info import levels_schedule, rewards_distribution
from ..engine.tables import TablesManager

from .utils import SessionUUID, get_session_and_user

manager = TablesManager()

router = APIRouter(prefix="/info", tags=["info"])


class TxnHistory(BaseModel):
    username: str | None
    sender_id: int | None
    txn_time: str | None
    txn_type: str | None
    txn_value: float | None
    balance: float | None
    image_id: int | None = None
    role: str | None


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


@router.get("/{club_id}/history", status_code=HTTP_200_OK,
            summary="Get a list of countries in different languages")
async def v1_get_history_trx(club_id: int, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        txn_history = await db.get_user_history_trx_in_club(user.id, club_id)
        print(txn_history)
        return [
            TxnHistory(
                username=(await db.get_user(txn.sender_id)).name,
                sender_id=txn.sender_id,
                txn_time=txn.created_ts.timestamp(),
                txn_type=txn.txn_type,
                txn_value=txn.txn_value,
                balance=txn.total_balance,
                role=(await db.find_account(user_id=txn.sender_id, club_id=club_id)).user_role,
                image_id=(await db.get_user(txn.sender_id)).image_id
            ) for txn in txn_history
        ]


@router.get("/{club_id}/balance_history", status_code=HTTP_200_OK,
            summary="Get a list of countries in different languages")
async def v1_get_balance_history_trx(club_id: int, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        txn_history = await db.get_user_balance_history_trx_in_club(user.id, club_id)
        return [
            TxnHistory(
                    username=(await db.get_user(txn.sender_id)).name,
                    sender_id=txn.sender_id,
                    txn_time=txn.created_ts.timestamp(),
                    txn_type=txn.txn_type,
                    txn_value=txn.txn_value,
                    balance=txn.total_balance,
                    role=(await db.find_account(user_id=txn.sender_id, club_id=club_id)).user_role,
                    image_id=(await db.get_user(txn.sender_id)).image_id
                ) for txn in txn_history
            ]