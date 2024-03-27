from fastapi import HTTPException
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND

from ..utils import SessionUUID, get_session_and_user
from ...db import DBI
from ...engine.info import levels_schedule
from ...engine.tables import TablesManager
from .router import *

manager = TablesManager()

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