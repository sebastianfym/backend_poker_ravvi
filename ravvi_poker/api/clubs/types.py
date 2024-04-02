import datetime
from _decimal import Decimal
from typing import Optional, Any, List

from psycopg.rows import Row
from pydantic import BaseModel, Field, field_validator, validator, constr
from pydantic.dataclasses import dataclass as pydantic_dataclass
from pydantic_core.core_schema import ValidationInfo


@pydantic_dataclass
class ErrorException(Exception):
    status_code: int
    detail: str
    message: str


class ClubProps(BaseModel):
    name: str | None = None
    description: str | None = None
    image_id: int | None = None
    timezone: str | None = None

    automatic_confirmation: bool | None = False


class ClubProfile(BaseModel):
    id: int
    name: str
    description: str | None = None
    image_id: int | None = None
    user_role: str | None = None
    user_approved: bool | None = None

    tables_count: int | None = 0
    players_count: int | None = 0
    user_balance: float | None = 0.00
    agents_balance: float | None = 0.00
    club_balance: float | None = 0.00
    service_balance: float | None = 0.00

    timezone: str | None = None

    automatic_confirmation: bool | None = False


class ClubMemberProfile(BaseModel):
    id: int | None = None
    username: str | None = None
    image_id: int | None = None
    user_role: str | None = None
    user_approved: bool | None = None
    country: str | None = None

    nickname: str | None = None
    balance: float | None = 00.00
    balance_shared: float | None = 00.00

    join_in_club: float | None = None
    leave_from_club: float | None = None

    last_session: float | None = None
    last_game: float | None = None

    winning: float | None = 00.00
    hands: float | None = 00.00
    user_comment: str | None = None

    agent_id: int | None = None

class SortingByDate(BaseModel):
    starting_date: float | None = None
    end_date: float | None = None


class UserRequest(BaseModel):
    id: int | None
    txn_id: int | None

    username: str | None
    image_id: int | None
    user_role: str | None
    nickname: str | None
    txn_value: float | None
    txn_type: str | None
    balance_type: str | None

    join_in_club: float | None
    leave_from_club: float | None

    country: str | None


class UnionProfile(BaseModel):
    name: str | None = None
    """По мере прогресса раширить модель"""


class MemberApplicationForMembership(BaseModel):
    user_comment: str | None = None


class AccountDetailInfo(BaseModel):
    join_datestamp: float | None
    timezone: str | None
    table_types: set | None
    game_types: set | None
    game_subtypes: set | None
    opportunity_leave: bool | None = True
    hands: float | None
    winning: float | None
    bb_100_winning: float | None
    now_datestamp: float | None
    balance: float | None = None


class MemberAccountDetailInfo(BaseModel):
    id: int
    join_datestamp: float | None
    last_session: float | None
    last_entrance_in_club: float | None
    last_game: float | None
    timezone: str | None
    opportunity_leave: bool | None = True
    nickname: str | None
    country: str | None
    username: str | None
    user_role: str | None
    club_comment: str | None
    balance: float | None
    balance_shared: float | None
    hands: float | None
    winning: float | None
    bb_100_winning: float | None
    now_datestamp: float | None
    rakeback_percentage: float | None = None
    rakeback: float | None = None
    commission: float | None = None


class ChangeMembersData(BaseModel):
    id: int
    nickname: str | None = None
    club_comment: str | None = None
    user_role: str | None = None

    @validator("user_role")
    def user_role_validate(cls, value):
        if value not in ['O', 'M', 'A', 'P', 'S']:
            raise ValueError('Operation must be either "approve" or "reject"')
        return value


class ChangeMembersAgent(BaseModel):
    # id: int
    agent_id: int | None = None


class ClubAgentProfile(BaseModel): #Todo изменить
    id: int | None = None
    username: str | None = None
    image_id: int | None = None
    user_role: str | None = None
    country: str | None = None
    nickname: str | None = None

    agent_id: int | None = None
    agents_count: int | None = None
    super_agents_count: int | None = None
    players: int | None = 0


class ClubChipsValue(BaseModel):
    amount: Decimal = Field(
        gt=0,
        lt=10 ** 10,
        decimal_places=2
    )

    @field_validator("amount", mode="before")
    @classmethod
    def ensure_not_str(cls, v: Any):
        if isinstance(v, str):
            raise ValueError
        return v


class UserChipsValue(ClubChipsValue):
    balance: str
    # ID пользователя (user_profile)
    account_id: int
    club_member: Row | None = Field(default=None)

    @field_validator("balance", mode="before")
    @classmethod
    def ensure_correct_type(cls, v: Any):
        if v not in ["balance", "balance_shared"]:
            raise ValueError
        return v


class ChipRequestForm(BaseModel):
    id: int
    operation: str

    @validator('operation')
    def operation_validate(cls, value):
        if value not in ["approve", "reject"]:
            raise ValueError('Operation must be either "approve" or "reject"')
        return value


class ChipsTxnItem(BaseModel):
    id: int
    created_ts: float
    created_by: int
    txn_type: str
    amount: Decimal
    balance: Decimal | None = None
    ref_user_id: int | None = None
    ref_agent_id: int | None = None


class ClubBalance(BaseModel):
        club_balance: float | None
        members_balance: float | None
        agents_balance: float | None
        total_balance: float | None


class ClubHistoryTransaction(BaseModel):
    txn_type: str | None
    txn_value: float | None
    txn_time: float | None
    recipient_id: int | None
    recipient_name: str | None
    recipient_nickname: str | None
    recipient_country: str | None
    recipient_role: str | None

    sender_id: int | None
    sender_name: str | None
    sender_nickname: str | None
    sender_country: str | None
    sender_role: str | None
    balance_type: str | None


class UserRequestsToJoin(BaseModel):
    rakeback: int | None = None
    agent_id: int | None = None
    nickname: str | None = None
    comment: str | None = None
    user_role: str | None = "P"

    @validator("user_role")
    def user_role_validate(cls, value):
        if value not in ['O', 'M', 'A', 'P', 'S']:
            raise ValueError('Operation must be either "approve" or "reject"')
        return value

# TABLES

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

# HistoryModel

class TxnHistoryManual(BaseModel):
    username: str | None
    sender_id: int | None
    txn_time: str | None
    txn_type: str | None
    txn_value: float | None
    balance: float | None
    image_id: int | None = None
    role: str | None


class TxnHistoryOnTable(BaseModel):
    username: str | None
    table_name: str | None
    table_id: int | None
    txn_time: str | None
    min_blind: float | None
    max_blind: float | None
    txn_type: str | None
    txn_value: float | None
    balance: float | None
