from decimal import Decimal
from datetime import datetime as DateTime
from starlette.status import HTTP_200_OK
from pydantic import BaseModel, field_validator

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

    @field_validator("created_ts", mode="before")
    @classmethod
    def timestamp(cls, value) -> float:
        if isinstance(value, DateTime):
            value = value.timestamp()
        return value


class MemberInfo(UserPublicProfile):
    nickname: str | None = None
    user_role: str | None = None


class ClubTxnHistory(BaseModel, extra="forbid"):
    txns: list[ClubTxnItem]
    users: list[MemberInfo]


@router.get(
    "/{club_id}/txns/club",
    status_code=HTTP_200_OK,
    responses={
        400: {"model": ErrorException, "description": "Invalid request params"},
        403: {"model": ErrorException, "description": "No permission"},
        404: {"model": ErrorException, "description": "Club not found"},
    },
    summary="Получить список транзакций в клубе",
)
async def v1_txns_club(club_id: int, session_uuid: SessionUUID) -> ClubTxnHistory:
    """ """

    async with DBI() as db:
        _, user = await get_session_and_user(db, session_uuid)
        club, _ = await get_club_and_member(db, club_id=club_id, user_id=user.id, roles_required=["O", "M", "A", "S"])
        # CHECKS

        _txns = await db.get_club_txns(club_id=club.id)
        _members = await db.get_club_members(club_id=club.id)

    users = set()
    txns = []
    for x in _txns:
        users.add(x.created_by)
        if x.user_id is not None:
            users.add(x.user_id)
        txns.append(
            ClubTxnItem(
                created_ts=x.created_ts,
                created_by=x.created_by,
                txn_id=x.txn_id,
                txn_type=x.txn_type,
                txn_delta=x.txn_delta,
                balance=x.balance,
                user_id=x.user_id,
            )
        )

    users = [
        MemberInfo(
            id=m.user_id, name=m.name, image_id=m.image_id, country=m.country, nikname=m.nickname, user_role=m.user_role
        )
        for m in _members
        if m.user_id in users
    ]

    return ClubTxnHistory(txns=txns, users=users)
