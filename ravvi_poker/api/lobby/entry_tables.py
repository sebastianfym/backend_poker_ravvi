from typing import List

from .router import *
from ..clubs.types import TableParams
from ..utils import SessionUUID, get_session_and_user
from ...db import DBI


@router.get("/entry_tables", status_code=200, summary="Get game entry points")
async def v1_get_entry_tables(session_uuid: SessionUUID) -> List[TableParams]:
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        tables = await db.get_lobby_entry_tables()
    return list([
        TableParams(
            id=table.id,
            club_id=table.club_id,
            table_name=table.table_name,
            table_type=table.table_type,
            table_seats=table.table_seats,
            game_type=table.game_type,
            game_subtype=table.game_subtype
        ) for table in tables
    ])