import datetime
from typing import Any, Optional, List

from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from pydantic_core.core_schema import ValidationInfo
from starlette.status import HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND
from pydantic import BaseModel, model_validator, field_validator, constr, Field

from ..db import DBI
from ..engine.tables import TablesManager

from .utils import SessionUUID, get_session_and_user

manager = TablesManager()

router = APIRouter(prefix="/tables", tags=["tables"])


class TableParams(BaseModel):
    table_type: str | None = None
    table_seats: int = Field(ge=2, le=9)
    table_name: str | None = None
    game_type: str | None = None
    game_subtype: str | None = None

    players_required: int | None = 2
    mtt_type: str | None = None
    buyin_min: float | None = None
    buyin_max: float | None = None
    spin_multiplier: float | None = None
    buyin_cost: float | None = None
    buyin_value: int | None = None
    registration_time: int | None = None
    rebuy_cost: float | None = None
    rebuy_value: int | None = None
    rebuy_count: int | None = None
    addon_cost: float | None = None
    addon_value: int | None = None
    rewards_structure: str | None = None
    blind_small: float | None = None
    blind_big: float | None = None
    ante: float | None = None
    level_schedule: str | None = None
    level_time: int | None = None
    action_time: int | None = None
    club_fee: int | None = None
    club_fee_cap: int | None = None
    jackpot: bool | None = None
    ante_up: bool | None = None
    double_board: bool | None = None
    bombpot_freq: int | None = None
    bombpot_min: int | None = None
    bombpot_max: int | None = None
    bombpot_double_board: bool | None = None
    seven_deuce: int | None = None
    hi_low: bool | None = None
    vpip_level: int | None = None
    vpip_threshold: int | None = None
    call_time: int | None = None
    call_time_type: str | None = None
    chat_mode: str | None = None
    access_password: Optional[constr(min_length=4, max_length=4)] = None
    access_manual: bool | None = None
    deny_countries: Optional[List[str]] | None = []
    deny_clubs: Optional[List[str]] | None = []
    deny_unions: Optional[List[str]] | None = []
    gps: bool | None = None
    ip: bool | None = None
    disable_pc: bool | None = None
    email_restriction: bool | None = None
    captcha: bool | None = False
    view_during_move: bool | None = False
    run_multi_times: bool | None = None
    ev_chop: bool | None = False
    ratholing: int | None = None
    withdrawals: bool | None = None
    drop_card_round: Optional[str] | None = None


    @field_validator('table_type')
    @classmethod
    def check_table_type(cls, table_type: str, info: ValidationInfo) -> str:
        try:
            match table_type:
                case "RG":
                    return table_type
                case "SNG":
                    return table_type
                case "MTT":
                    return table_type
                case "FLASH":
                    return table_type
                case "SPIN":
                    return table_type
                case _:
                    raise ValueError(f'Possible options: RG | SNG | MTT')
        except KeyError:
            raise ValueError(f'There is no suitable value for table_type')

    @field_validator('game_type')
    @classmethod
    def check_game_type(cls, game_type: str, info: ValidationInfo) -> str:
        try:
            match game_type:
                case "NLH":
                    return game_type
                case "PLO":
                    return game_type
                case "OFC":
                    return game_type
                case _:
                    raise ValueError(f'Possible options: NLH | PLO | OFC')
        except KeyError:
            raise ValueError(f'There is no suitable value for game_type')

    @field_validator('game_subtype')
    @classmethod
    def check_game_subtype(cls, game_subtype: str, info: ValidationInfo) -> str:
        try:
            game_type = info.data['game_type']
            match game_type:
                case "NLH":
                    match game_subtype:
                        case "REGULAR" | "AOF" | "3-1" | "6+":
                            return game_subtype
                        case _:
                            raise ValueError(f'Possible options: REGULAR | AOF | 3-1 | 6+.')  # eng | status_code
                case "PLO":
                    match game_subtype:
                        case "PLO4" | "PLO5" | "PLO6":
                            return game_subtype
                        case _:
                            raise ValueError(f'Possible options: PLO4 | PLO5 | PLO6.')
                case "OFC":
                    match game_subtype:
                        case "DEFAULT":
                            return game_subtype
                        case _:
                            return ValueError(f'Possible options: DEFAULT.')
        except KeyError:
            raise ValueError(f'There is no suitable value for game_subtype')

    @field_validator("ratholing")
    @classmethod
    def check_ratholing(cls, ratholing: int) -> int:
        if ratholing:
            if 0 <= ratholing <= 12:
                return ratholing
            else:
                raise ValueError(f'Invalid ratholing, must be between 0 and 12')

    @field_validator("level_time")
    @classmethod
    def check_level_time(cls, level_time: int, info: ValidationInfo) -> int:
        table_type = info.data['table_type']
        try:
            match table_type:
                case "SNG" | "MTT":
                    if 1 <= level_time <= 30:
                        return level_time
                    else:
                        raise ValueError(f'level_time must be between 2 and 30')
                case "SPIN":
                    if 1 <= level_time <= 6 or None:
                        return level_time
                    else:
                        raise ValueError(f'level_time must be between 2 and 6')
                case _:
                    return None
        except TypeError:
            return None

    @field_validator("chat_mode")
    @classmethod
    def check_chat_mode(cls, chat_mode: str) -> int:
        match chat_mode:
            case "DISABLE" | "PLAYERS" | "ALL":
                return chat_mode
            case _:
                return None

    @field_validator("drop_card_round")
    @classmethod
    def check_drop_card_round(cls, drop_card_round: str, info: ValidationInfo):
        game_subtype = info.data["game_subtype"]
        if game_subtype != "3-1" and drop_card_round:
            raise ValueError("only NLH 3-1 support drop_card_round")
        elif game_subtype == "3-1" and drop_card_round not in ["PREFLOP", "FLOP"]:
            raise ValueError("incorrect round for drop card in NLH 3-1")
        return drop_card_round


class TableProfile(TableParams):
    id: int | None = None
    club_id: int | None = None
    players_count: int | None = None
    viewers_count: int | None = None
    created: Optional[datetime.datetime] = None
    opened: Optional[datetime.datetime] = None
    closed: Optional[datetime.datetime] = None
    prize_fund: int | None = None


@router.get("/{table_id}/result", status_code=200, summary="Get table (SNG/MTT) result")
async def v1_get_table_result(table_id: int, session_uuid: SessionUUID):
    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        table = await db.get_table(table_id)
        if not table:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Table not found")
        if table.table_type not in ('SNG', 'MTT'):
            raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Table not found")
        rows = await db.get_table_result(table_id)
        rows.sort(key=lambda x: x.balance_end or x.balance_begin or 0, reverse=True)
        result = []
        for i, r in enumerate(rows, start=1):
            x = dict(
                user_id=r.user_id,
                username=r.username,
                image_id=r.image_id,
                reward=r.balance_end,
                rank=i
            )
            result.append(x)
    return dict(result=result)
