from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND
from pydantic import BaseModel

from ..db.dbi import DBI
from .auth import RequireSessionUUID, get_session_and_user

from .clubs import router as clubs_router

router = APIRouter(prefix="/tables", tags=["tables"])


class TableCreate(BaseModel):
    table_name: str
    table_type: str | None = None
    table_seats: int
    game_type: str
    game_subtype: str | None = None


class TableProfile(BaseModel):
    id: int
    club_id: int
    table_name: str | None
    table_type: str | None
    table_seats: int | None
    game_type: str | None
    game_subtype: str | None


class TableProfileList(BaseModel):
    tables: list[TableProfile]


@clubs_router.get("/{club_id}/tables", response_model=TableProfileList, status_code=200,
                  summary="Get club tables")
async def v1_get_club_tables(club_id: int, session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        club = dbi.get_club(club_id)
        if not club:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND, detail="Club not found"
            )
        club_member = dbi.get_club_member(club.id, user.id)
        if not club_member:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Permission denied"
            )
        tables = dbi.get_tables_for_club(club_id=club_id)

    return TableProfileList(tables=[
        TableProfile(
            id=table.id,
            club_id=table.club_id,
            table_name=table.table_name,
            table_type=table.table_type,
            table_seats=table.table_seats,
            game_type=table.game_type,
            game_subtype=table.game_subtype,
        ) for table in tables
    ])


@clubs_router.post("/{club_id}/tables", response_model=TableProfile, status_code=201,
                   summary="Create club table")
async def v1_create_club_table(club_id: int, params: TableCreate,
                               session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        club = dbi.get_club(club_id)
        if not club:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND, detail="Club not found"
            )
        if club.founder_id != user.id:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Permission denied"
            )
        table = dbi.create_table(club_id=club_id, **params.model_dump())

    return TableProfile(
        id=table.id,
        club_id=table.club_id,
        table_name=table.table_name,
        table_type=table.table_type,
        table_seats=table.table_seats,
        game_type=table.game_type,
        game_subtype=table.game_subtype,
    )


@clubs_router.delete("/{club_id}/tables/{table_id}", response_model={}, status_code=204,
                     summary="Delete club table")
async def v1_delete_club_table(club_id: int, table_id: int,
                               session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        club = dbi.get_club(club_id)
        if not club:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND, detail="Club not found"
            )
        if club.founder_id != user.id:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN, detail="Permission denied"
            )
        table = dbi.get_table(table_id)
        if not table or table.club_id != club.id:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND, detail="Table not found"
            )
        dbi.delete_table(table.id)

    return {}


# @router.get("/{table_id}", response_model=TableProfile, summary="Get table by id")
# async def v1_get_table(table_id: int, session_uuid: RequireSessionUUID):
#     with DBI() as dbi:
#         session, user = get_session_and_user(dbi, session_uuid)
#         # TODO: access check
#         table = dbi.get_table(table_id)
#         if not table:
#             raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Table not found")

#     return TableProfile(
#         id=table.id,
#         club_id= table.club_id
#         )


# @router.put("/{table_id}", response_model=TableProfile, summary="Update table")
# async def v1_get_table(table_id: int, session_uuid: RequireSessionUUID):
#     with DBI() as dbi:
#         session, user = get_session_and_user(dbi, session_uuid)
#         # TODO: access check
#         table = dbi.get_table(table_id)
#         if not table:
#             raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Table not found")
#         # TODO: update profs

#     return TableProfile(
#         id=table.id,
#         club_id= table.club_id
#         )
