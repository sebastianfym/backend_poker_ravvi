from decimal import Decimal
from datetime import datetime as DateTime
from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN, HTTP_404_NOT_FOUND
from pydantic import BaseModel, field_validator
from fastapi.exceptions import HTTPException

from ...db import DBI
from ..utils import SessionUUID, get_session_and_user, get_club_and_member
from ..users.types import UserPublicProfile
from .types import ErrorException
from .router import router


class ClubTxnItem(BaseModel, extra="forbid"):
    txn_id: int
    txn_type: str
    txn_delta: Decimal
    balance: Decimal
    created_ts: float
    created_by: int
    user_id: int | None
    table_id: int | None

    @field_validator("created_ts", mode="before")
    @classmethod
    def timestamp(cls, value) -> float:
        if isinstance(value, DateTime):
            value = value.timestamp()
        return value


class MemberInfo(UserPublicProfile):
    nickname: str | None = None
    user_role: str | None = None

class TableInfo(BaseModel, extra="forbid"):
    id: int
    table_name: str|None
    blind_small: Decimal
    blind_big: Decimal
    

class ClubTxnHistory(BaseModel, extra="forbid"):
    txns: list[ClubTxnItem]
    users: list[MemberInfo]
    tables: list[TableInfo]


@router.get(
    "/{club_id}/txns/player",
    status_code=HTTP_200_OK,
    responses={
        400: {"model": ErrorException, "description": "Invalid request params"},
        403: {"model": ErrorException, "description": "No permission"},
        404: {"model": ErrorException, "description": "Club not found"},
    },
    summary="Получить список транзакций в клубе",
)
async def v1_txns_player(club_id: int, session_uuid: SessionUUID) -> ClubTxnHistory:
    """ """

    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club = await db.get_club(club_id)
        if not club:
            raise HTTPException(status_code=HTTP_404_NOT_FOUND,
                                detail="Club not found")
        member = await db.find_member(club_id=club_id, user_id=user.id)
        if not member or member.approved_ts is None or member.closed_ts is not None:
            raise HTTPException(status_code=HTTP_403_FORBIDDEN,
                                detail="You are not club member")

        _txns = await db.get_player_txns(member_id=member.id)
        users = {x.created_by for x in _txns if x.created_by} | {x.user_id for x in _txns if x.user_id}

        tables = {x.ref_table_id for x in _txns if x.ref_table_id}
        tables = [db.get_table(table_id) for table_id in tables]

        _members = await db.get_club_members(club_id=club.id)

    txns = []
    for x in _txns:
        txns.append(
            ClubTxnItem(
                created_ts=x.created_ts,
                created_by=x.created_by,
                txn_id=x.txn_id,
                txn_type=x.txn_type,
                txn_delta=x.txn_delta,
                balance=x.balance,
                user_id=x.user_id,
                table_id=x.ref_table_id
            )
        )

    users = [
        MemberInfo(
            id=m.user_id, name=m.name, image_id=m.image_id, country=m.country, nikname=m.nickname, user_role=m.user_role
        )
        for m in _members
        if m.user_id in users
    ]

    tables = [
        TableInfo(id = t.id, table_name=t.table_name, blind_small = t.props.get('blind_small'), blind_big = t.props.get('blind_big'))
        for t in tables
    ]

    return ClubTxnHistory(txns=txns, users=users, tables=tables)
