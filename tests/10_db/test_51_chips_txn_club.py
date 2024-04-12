import logging
import pytest
from decimal import Decimal

from ravvi_poker.db.dbi import DBI

from helpers.x_utils import check_timestamp_threshold

log = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_chips_club(club_and_owner):
    club, owner_user = club_and_owner
    async with DBI() as db:
        club = await db.get_club(club.id)
        owner_member = await db.find_member(club_id=club.id, user_id=owner_user.id)

    assert owner_member
    assert club.club_balance == 0
    assert owner_member.balance == 0

    # CHIPSIN -100.00
    with pytest.raises(DBI.Error) as ex:
        async with DBI() as db:
            await db.create_txn_CHIPSIN(txn_user_id=owner_user.id, club_id=club.id, txn_value=-100.0001)
    assert ex.value.code


    # CHIPSIN 100.00
    async with DBI() as db:
        txn_id = await db.create_txn_CHIPSIN(txn_user_id=owner_user.id, club_id=club.id, txn_value=100.0001)
        txn = await db.get_chips_txn(txn_id)
        club = await db.get_club(club.id)
        owner_member = await db.get_club_member(owner_member.id)

    assert txn
    assert txn.txn_id
    assert txn.txn_type == 'CHIPSIN'
    assert txn.txn_value == 100
    assert check_timestamp_threshold(txn.created_ts)
    assert txn.created_by == owner_user.id
    assert txn.club_id == club.id
    assert txn.member_id is None
    assert txn.user_id is None
    assert txn.ref_member_id is None
    assert txn.ref_user_id is None
    assert club.club_balance == Decimal('100.00')
    assert owner_member.balance == 0

    # CHIPSOUT -42.05
    async with DBI() as db:
        txn_id = await db.create_txn_CHIPSOUT(txn_user_id=owner_user.id, club_id=club.id, txn_value=42.0499)
        txn = await db.get_chips_txn(txn_id)
        club = await db.get_club(club.id)
        owner_member = await db.get_club_member(owner_member.id)

    assert txn
    assert txn.txn_id
    assert txn.txn_type == 'CHIPSOUT'
    assert txn.txn_value == Decimal('42.05')
    assert check_timestamp_threshold(txn.created_ts)
    assert txn.created_by == owner_user.id
    assert txn.club_id == club.id
    assert txn.member_id is None
    assert txn.user_id is None
    assert txn.ref_member_id is None
    assert txn.ref_user_id is None

    assert club.club_balance == Decimal('57.95')
    assert owner_member.balance == 0

    # CHIPSOUT <too much>
    with pytest.raises(DBI.Error) as ex:
        async with DBI() as db:
            await db.create_txn_CHIPSOUT(txn_user_id=owner_user.id, club_id=club.id, txn_value=666.0123)
    assert ex.value.code

    async with DBI() as db:
        club = await db.get_club(club.id)
        owner_member = await db.get_club_member(owner_member.id)
    assert club.club_balance == Decimal('57.95')
    assert owner_member.balance == 0

    # check list
    async with DBI() as db:
        txns = await db.get_club_txns(club_id=club.id)
    txns.sort(key=lambda x: x.txn_id)

    assert len(txns) == 2

    x = txns[0]
    assert x.txn_id
    assert x.created_ts
    assert x.created_by == owner_user.id
    assert x.txn_type == 'CHIPSIN'
    assert x.txn_delta == Decimal('100.00')
    assert x.balance == Decimal('100.00')


    x = txns[1]
    assert x.txn_id
    assert x.created_ts
    assert x.created_by == owner_user.id
    assert x.txn_type == 'CHIPSOUT'
    assert x.txn_delta == Decimal('-42.05')
    assert x.balance == Decimal('57.95')


