from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, field_validator
from fastapi import HTTPException
from starlette.status import HTTP_400_BAD_REQUEST

from pydantic.dataclasses import dataclass as pydantic_dataclass


@pydantic_dataclass
class ErrorException(Exception):
    status_code: int
    detail: str
    message: str


class ChipsActionParams(BaseModel, extra="forbid"):
    action: str
    amount: float | Decimal

    @field_validator("action", mode="before")
    @classmethod
    def valid_action(cls, value: str) -> str:
        if not isinstance(value, str):
            raise ValueError("no action provided")
        value = value.upper()
        return value

    @field_validator("amount", mode="before")
    @classmethod
    def not_zero(cls, value) -> Decimal:
        value = Decimal(value)
        if value <= 0:
            raise ValueError("invalid value")
        return value


class ChipsTxnInfo(BaseModel, extra="forbid"):
    txn_id: int


class ChipsParams(BaseModel):
    amount: Decimal | str

    @field_validator("amount", mode="after")
    def not_zero(cls, value: float | Decimal | str) -> Decimal | str:
        if value == "all":
            return value
        else:
            value = round(value, 2)
            # if value <= 0:
            #     raise HTTPException(HTTP_400_BAD_REQUEST, "Invalid value")
            return value


class BalanceMode(str, Enum):
    PICK_UP = "pick_up"
    GIVE_OUT = "give_out"


# class ChipsParamsForAgents(ChipsParams):
#     mode: BalanceMode
#
#     @field_validator("mode")
#     def only_two_choice(cls, mode: str):
#         match mode:
#             case "pick_up":
#                 return mode
#             case "give_out":
#                 return mode
#             case _:
#                 raise ValueError(f'Possible options: pick_up | give_out')


class ChipsParamsForMembers(ChipsParams):
    # mode: str
    club_member: list

    # @field_validator("mode")
    # def only_two_choice(cls, mode: str):
    #     match mode:
    #         case "pick_up":
    #             return mode
    #         case "give_out":
    #             return mode
    #         case _:
    #             raise ValueError(f'Possible options: pick_up | give_out')


class ChipsTxnItem(BaseModel):
    txn_id: int
    txn_type: str
    created_ts: float
    created_by: int
    delta: Decimal
    balance: Decimal


class ChipsRequestParams(ChipsParams):
    agent: bool


class ChipsRequestItem(BaseModel):
    id: int
    created_ts: float
    created_by: int
    txn_type: str
    amount: Decimal
    closed_ts: float | None = None
    closed_by: int | None = None


class ChipsRequestAction(BaseModel):
    action: str

    @field_validator("action")
    def check_value(cls, action: str) -> str:
        if action == "approve":
            return action
        elif action == "reject":
            return action
        else:
            raise ValueError("Action must  be only: approve, reject")


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


class ChipRequestForm(BaseModel):
    operation: str

    @field_validator("operation")
    def operation_validate(cls, value):
        if value not in ["approve", "reject"]:
            raise ValueError('Operation must be either "approve" or "reject"')
        return value
