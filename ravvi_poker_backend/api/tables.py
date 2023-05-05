from typing import Annotated, Optional, List

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_404_NOT_FOUND
from pydantic import BaseModel
from . import utils

from ..db.dbi import DBI
from .auth import RequireSessionUUID, get_session_and_user

from .clubs import router as clubs_router

router = APIRouter(prefix="/tables", tags=["tables"])


class TableProps(BaseModel):
    description: str|None = None

class TableProfile(BaseModel):
    id: int
    club_id: int


@clubs_router.post("/{club_id}/tables", response_model=TableProfile, summary="Create poker table in the club")
async def v1_create_club_table(club_id: int, params: TableProps, session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        session, user = get_session_and_user(dbi, session_uuid)
        club = dbi.get_club(club_id)
        if club.founder_id!=user.id:
            # TODO: proper error code
            raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail="Invalid role")
        table = dbi.create_table(club_id=club_id)
    
    return TableProfile(
        id=table.id, 
        club_id=table.club_id
        )


@clubs_router.get("/{club_id}/tables", response_model=List[TableProfile], summary="List tables in the club")
async def v1_list_club_tables(club_id: int, session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        session, user = get_session_and_user(dbi, session_uuid)
        club = dbi.get_club(club_id)
        # TODO: club validation & access check
        tables = dbi.get_tables_for_club(club_id=club_id)
    
    tables = [
        TableProfile(
            id=x.id, 
            club_id=x.club_id
        )
        for x in tables
    ]

    return tables

@router.get("/{table_id}", response_model=TableProfile, summary="Get table by id")
async def v1_get_table(table_id: int, session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        session, user = get_session_and_user(dbi, session_uuid)
        # TODO: access check
        table = dbi.get_table(table_id)
        if not table:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Table not found")
    
    return TableProfile(
        id=table.id,
        club_id= table.club_id
        )

@router.put("/{table_id}", response_model=TableProfile, summary="Update table")
async def v1_get_table(table_id: int, session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        session, user = get_session_and_user(dbi, session_uuid)
        # TODO: access check
        table = dbi.get_table(table_id)
        if not table:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Table not found")
        # TODO: update profs
    
    return TableProfile(
        id=table.id,
        club_id= table.club_id
        )
