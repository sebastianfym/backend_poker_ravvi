from typing import Any

from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND
from pydantic import BaseModel, model_validator, field_validator

from ..db.dbi import DBI
from .auth import RequireSessionUUID, get_session_and_user

from .clubs import router as clubs_router

router = APIRouter(prefix="/tables", tags=["tables"])

class TableCreate(BaseModel):
    table_name: str | None = None
    table_type: str
    table_seats: int
    game_type: str
    game_subtype: str
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

class TableProps(TableCreate):
    id: int
    club_id: int | None

@clubs_router.get("/{club_id}/tables", status_code=200, summary="Get club tables")
async def v1_get_club_tables(club_id: int, session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        club = dbi.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        club_member = dbi.get_club_member(club.id, user.id)
        if not club_member:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Permission denied"
            )
        tables = dbi.get_tables_for_club(club_id=club_id)

    return list([TableProps(**t) for t in tables])

@clubs_router.post("/{club_id}/tables", status_code=201, summary="Create club table")
async def v1_create_club_table(club_id: int, params: TableCreate, session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        club = dbi.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        if club.founder_id != user.id:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Permission denied")
        props = params.model_dump(exclude_unset=False)
        table = dbi.create_table(club_id=club_id, **props)

    return TableProps(**table)
