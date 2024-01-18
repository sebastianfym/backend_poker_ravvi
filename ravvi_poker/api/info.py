from fastapi import APIRouter, HTTPException
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND

from ..db import DBI
from ..engine.info import levels_schedule, rewards_distribution
from ..engine.tables import TablesManager

from .utils import SessionUUID, get_session_and_user

manager = TablesManager()

router = APIRouter(prefix="/info", tags=["info"])


@router.get("/levels_schedule/{table_type}/{schedule_type}", status_code=HTTP_200_OK, summary="Get blind levels schedule (SNG/MTT)")
async def v1_get_all_info_about_blinds(table_type: str, schedule_type: str, session_uuid: SessionUUID):
    """
    Возвращает список уровнией для турниров.

    table_type - тип стола: SNG | MTT.

    schedule_type - тип расписания:  STANDARD | TURBO | HYPERTURBO(MTT only)
    """

    table_type = table_type.lower()
    schedule_type = schedule_type.lower()

    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
    try:
        return levels_schedule[table_type][schedule_type]
    except KeyError:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Key not found")
    

@router.get("/rewards_distribution", status_code=HTTP_404_NOT_FOUND, summary="Get rewards distribution structure")
async def v1_get_payment_structure(session_uuid: SessionUUID):
    """
    Получаем структуру распределения выигрыша в турнирах.
    """
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)

    return rewards_distribution

