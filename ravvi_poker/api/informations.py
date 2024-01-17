from fastapi import APIRouter, HTTPException
from ..db import DBI
from ..engine.api_extra_data import blinds_information, payment_structure
from ..engine.tables import TablesManager

from .utils import SessionUUID, get_session_and_user



manager = TablesManager()

router = APIRouter(prefix="/info", tags=["info"])


@router.get("/{blinds_type}/{blinds_structure}/blinds_info", status_code=200, summary="Get table (SNG/MTT) result")
async def v1_get_all_info_about_blinds(session_uuid: SessionUUID, blinds_structure: str, blinds_type: str):
    """
    Получаем значения из таблицы о блиндах.

    blinds_type - тип блиндов (sng (можно spinup) или mtt).

    blinds_structure - структура блиндов (стандарт или турбо (для mtt ещще есть гипер турбо)).

    Возвращает список вида [[1, "25/50", 0], [2, "50/75", 1], ...].
    """

    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
    try:
        return blinds_information[blinds_type][blinds_structure]
    except KeyError:
        return HTTPException(status_code=404, detail="Key not found")

@router.get("/payment structure", status_code=200, summary="Get payment structure")
async def v1_get_payment_structure(session_uuid: SessionUUID):
    """
    Получаем значения из таблицы о выигрышах.
    """
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)

    return payment_structure

