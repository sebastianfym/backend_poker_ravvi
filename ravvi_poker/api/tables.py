from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND
from pydantic import BaseModel, FieldValidationInfo, model_validator, field_validator

from ..db.dbi import DBI
from .auth import RequireSessionUUID, get_session_and_user

from .clubs import router as clubs_router

router = APIRouter(prefix="/tables", tags=["tables"])


class GameSettings(BaseModel):
    ante: float | None = None
    big_blind: float | None = None
    buy_in: float | list[float]
    min_stack: float | None = None

    @field_validator("buy_in")
    def validate_buy_in(cls, v):
        if isinstance(v, list):
            if len(v) != 2:
                raise ValueError("Must contain only 2 values")
            if v[0] >= v[1]:
                raise ValueError("First value must be less than second")
        return v


class NLHGameSettings(GameSettings):
    @field_validator("big_blind")
    def validate_big_blind(cls, v, info: FieldValidationInfo):
        game_subtype = info.context.get("game_subtype")
        if not game_subtype == "6+":
            if v is None:
                raise ValueError("Must contain value")
            return v

    @field_validator("ante")
    def validate_ante(cls, v, info: FieldValidationInfo):
        game_subtype = info.context.get("game_subtype")
        if game_subtype == "6+":
            if v is None:
                raise ValueError("Must contain value")
        return v

    @field_validator("buy_in")
    def validate_buy_in(cls, v, info: FieldValidationInfo):
        game_subtype = info.context.get("game_subtype")
        if game_subtype == "AOF":
            if isinstance(v, list):
                raise ValueError("Must be float")
        else:
            if not isinstance(v, list):
                raise ValueError("Must be list")
        return v


class PLOGameSettings(GameSettings):
    @field_validator("big_blind")
    def validate_big_blind(cls, v):
        if v is None:
            raise ValueError("Must contain value")
        return v

    @field_validator("buy_in")
    def validate_buy_in(cls, v):
        if not isinstance(v, list):
            raise ValueError("Must be list")
        return v


class OFCGameSettings(GameSettings):
    @field_validator("big_blind")
    def validate_big_blind(cls, v):
        if v is None:
            raise ValueError("Must contain value")
        return v

    @field_validator("buy_in")
    def validate_buy_in(cls, v):
        if not isinstance(v, list):
            raise ValueError("Must be list")
        return v

    @field_validator("min_stack")
    def validate_min_stack(cls, v):
        if v is None:
            raise ValueError("Must contain value")
        return v


class TableCreate(BaseModel):
    table_name: str | None = None
    table_type: str | None = None
    table_seats: int
    game_type: str
    game_subtype: str | None = None
    game_settings: GameSettings

    @field_validator("game_type")
    def validate_game_type(cls, v):
        if v not in GAME_TYPES_SETTINGS.keys():
            raise ValueError("No such game type")
        return v

    @model_validator(mode="after")
    def validate_game_settings(cls, data):
        settings_model = GAME_TYPES_SETTINGS.get(data.game_type)
        context = {
            "game_type": data.game_type,
            "game_subtype": data.game_subtype,
        }
        settings_model.model_validate(
            data.game_settings.model_dump(), context=context
        )
        return data


GAME_TYPES_SETTINGS = {
    "NLH": NLHGameSettings,
    "PLO": PLOGameSettings,
    "OFC": OFCGameSettings,
}


class TableProfile(BaseModel):
    id: int
    club_id: int
    table_name: str | None
    table_type: str | None
    table_seats: int | None
    game_type: str | None
    game_subtype: str | None


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

    return list([
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


@clubs_router.post("/{club_id}/tables", status_code=201, summary="Create club table")
async def v1_create_club_table(club_id: int, params: TableCreate, session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        club = dbi.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        if club.founder_id != user.id:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Permission denied")
        table_params = params.model_dump(exclude_unset=True)
        game_settings = params.game_settings.model_dump_json(exclude_unset=True)
        table_params["game_settings"] = game_settings
        table = dbi.create_table(club_id=club_id, **table_params)

    return TableProfile(
        id=table.id,
        club_id=table.club_id,
        table_name=table.table_name,
        table_type=table.table_type,
        table_seats=table.table_seats,
        game_type=table.game_type,
        game_subtype=table.game_subtype,
    )


@clubs_router.delete("/{club_id}/tables/{table_id}", status_code=204, summary="Delete club table")
async def v1_delete_club_table(club_id: int, table_id: int, session_uuid: RequireSessionUUID):
    with DBI() as dbi:
        _, user = get_session_and_user(dbi, session_uuid)
        club = dbi.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Club not found")
        if club.founder_id != user.id:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Permission denied")
        table = dbi.get_table(table_id)
        if not table or table.club_id != club.id:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Table not found")
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
