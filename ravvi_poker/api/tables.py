from typing import Any

from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND
from pydantic import BaseModel, model_validator, field_validator

from ..db import DBI
from ..engine.tables import TablesManager

from .utils import SessionUUID, get_session_and_user

manager = TablesManager()

router = APIRouter(prefix="/tables", tags=["tables"])

class TableProps(BaseModel):
    buyin_min: float | None = None
    buyin_max: float | None = None
    buyin_cost: float | None = None
    buyin_value: int | None = None
    late_entry_level: int | None = None
    rebuy_cost: float | None = None
    rebuy_value: int | None = None
    rebuy_count: int | None = None
    addon_cost: float | None = None
    addon_value: int | None = None
    addon_level: int | None = None
    blind_value: float | None = None
    blind_schedule: str | None = None
    blind_level_time: int | None = None

    jackpot: bool | None = None
    ante_up: bool | None = None
    double_board: bool | None = None
    bomb_pot: bool | None = None
    every_hand: int | None = None
    bomb_pot_ante_min: int | None = None
    bomb_pot_ante_max: int | None = None
    bomb_pot_triggers_double_board: bool | None = None
    seven_deuce: bool | None = None
    each_prize: int | None = None
    hi_low: bool | None = None

    vpip_level: int | None = None
    hand_threshold: int | None = None
    call_time: int | None = None
    call_time_type: str | None = None
    online_players: int | None = None

    gps: bool | None = None
    ip: bool | None = None
    disable_pc: bool | None = None
    email_restriction: bool | None = None
    access_manual: bool | None = None
    chat_mode: str | None = None
    access_countries: list[str] | None = []
    access_clubs: list[str] | None = []
    access_unions: list[str] | None = []


class TableParams(BaseModel):
    table_name: str | None = None
    table_type: str
    table_seats: int
    game_type: str
    game_subtype: str
    props: TableProps | None = None

class TableProfile(TableParams):
    id: int|None = None
    club_id: int | None = None


@router.get("/{table_id}/result", status_code=200, summary="Get table (SNG/MTT) result")
async def v1_get_table_result(table_id: int, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        table = await db.get_table(table_id)
        if not table:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Table not found")
        if table.table_type not in ('SNG','MTT'):
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Table not found")
        rows = await db.get_table_result(table_id)
        rows.sort(key=lambda x: x.balance_end or x.balance_begin or 0, reverse=True) 
        result = []
        for i, r in enumerate(rows, start=1):
            x = dict(
                user_id=r.user_id, 
                username=r.username, 
                image_id=r.image_id, 
                reward = r.balance_end,
                rank = i
            )
            result.append(x)
    return dict(result=result)