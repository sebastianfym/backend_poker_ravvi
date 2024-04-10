import logging
import pytest
from decimal import Decimal

from ravvi_poker.db.dbi import DBI

from helpers.x_utils import check_timestamp_threshold

log = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_chips_agent(club_and_owner, users_10):
    club, owner_user = club_and_owner
    user_1, user_2 = users_10[:2]
    async with DBI() as db:
        club = await db.get_club(club.id)
        owner_member = await db.find_member(club_id=club.id, user_id=owner_user.id)
        agent_1 = await db.create_club_member(club_id=club.id, user_id=user_1.id)
        await db.approve_club_member(agent_1.id, owner_user.id, user_role='A', club_comment=None, nickname=None)
        agent_2 = await db.create_club_member(club_id=club.id, user_id=user_2.id)
        await db.approve_club_member(agent_2.id, owner_user.id, user_role='A', club_comment=None, nickname=None)

    assert owner_member
    assert club.club_balance == 0
    assert owner_member.balance == 0
    assert agent_1.balance == 0
    assert agent_1.balance_shared == 0
    assert agent_2.balance == 0
    assert agent_2.balance_shared == 0

    # MOVIN 100.00 - not enough balance in club
    with pytest.raises(DBI.Error) as ex:
        async with DBI() as db:
            await db.create_txn_MOVEIN(txn_user_id=owner_user.id, club_id=club.id, member_id=agent_1.id, ref_member_id=None, txn_value=100)

    # add 100 to club
    async with DBI() as db:
        txn = await db.create_txn_CHIPSIN(txn_user_id=owner_user.id, club_id=club.id, txn_value=100.0001)

    # try again
    async with DBI() as db:
        await db.create_txn_MOVEIN(txn_user_id=owner_user.id, club_id=club.id, member_id=agent_1.id, ref_member_id=None, txn_value=50)
        club = await db.get_club(club.id)
        owner_member = await db.get_club_member(owner_member.id)
        agent_1 = await db.get_club_member(agent_1.id)
        agent_2 = await db.get_club_member(agent_2.id)

    assert club.club_balance == Decimal('50')
    assert owner_member.balance == 0
    assert agent_1.balance == 0
    assert agent_1.balance_shared == Decimal('50')
    assert agent_2.balance == 0
    assert agent_2.balance_shared == 0


    # MOVIN 100.00 - not enough balance_shared on agent 1
    with pytest.raises(DBI.Error) as ex:
        async with DBI() as db:
            await db.create_txn_MOVEIN(txn_user_id=owner_user.id, club_id=club.id, member_id=agent_2.id, ref_member_id=agent_1.id, txn_value=100)
    #log.error("%s", ex.value.msg)

    async with DBI() as db:
        await db.create_txn_MOVEIN(txn_user_id=owner_user.id, club_id=club.id, member_id=agent_2.id, ref_member_id=agent_1.id, txn_value=20)
        club = await db.get_club(club.id)
        owner_member = await db.get_club_member(owner_member.id)
        agent_1 = await db.get_club_member(agent_1.id)
        agent_2 = await db.get_club_member(agent_2.id)

    assert club.club_balance == Decimal('50')
    assert owner_member.balance == 0
    assert agent_1.balance == 0
    assert agent_1.balance_shared == Decimal('30')
    assert agent_2.balance == 0
    assert agent_2.balance_shared == Decimal('20')


    # MOVEOUT 100.00 - not enough balance_shared on agent 2
    with pytest.raises(DBI.Error) as ex:
        async with DBI() as db:
            await db.create_txn_MOVEOUT(txn_user_id=owner_user.id, club_id=club.id, member_id=agent_2.id, ref_member_id=agent_1.id, txn_value=100)

    async with DBI() as db:
        await db.create_txn_MOVEOUT(txn_user_id=owner_user.id, club_id=club.id, member_id=agent_2.id, ref_member_id=agent_1.id, txn_value=15)
        club = await db.get_club(club.id)
        owner_member = await db.get_club_member(owner_member.id)
        agent_1 = await db.get_club_member(agent_1.id)
        agent_2 = await db.get_club_member(agent_2.id)

    assert club.club_balance == Decimal('50')
    assert owner_member.balance == 0
    assert agent_1.balance == 0
    assert agent_1.balance_shared == Decimal('45')
    assert agent_2.balance == 0
    assert agent_2.balance_shared == Decimal('5')

    # MOVEOUT 100.00 - not enough balance_shared on agent 1
    with pytest.raises(DBI.Error) as ex:
        async with DBI() as db:
            await db.create_txn_MOVEOUT(txn_user_id=owner_user.id, club_id=club.id, member_id=agent_1.id, ref_member_id=None, txn_value=100)

    async with DBI() as db:
        await db.create_txn_MOVEOUT(txn_user_id=owner_user.id, club_id=club.id, member_id=agent_1.id, ref_member_id=None, txn_value=30)
        club = await db.get_club(club.id)
        owner_member = await db.get_club_member(owner_member.id)
        agent_1 = await db.get_club_member(agent_1.id)
        agent_2 = await db.get_club_member(agent_2.id)

    assert club.club_balance == Decimal('80')
    assert owner_member.balance == 0
    assert agent_1.balance == 0
    assert agent_1.balance_shared == Decimal('15')
    assert agent_2.balance == 0
    assert agent_2.balance_shared == Decimal('5')

    # check txn history for club
    async with DBI() as db:
        txns = await db.get_club_txns(club_id=club.id)
    assert len(txns) == 3

    txns.sort(key=lambda x: x.txn_id)

    x = txns[0]
    assert x.txn_id
    assert x.created_ts
    assert x.created_by == owner_user.id
    assert x.txn_type == 'CHIPSIN'
    assert x.txn_delta == Decimal('100')
    assert x.balance == Decimal('100')

    x = txns[1]
    assert x.txn_id
    assert x.created_ts
    assert x.created_by == owner_user.id
    assert x.txn_type == 'MOVEIN'
    assert x.txn_delta == Decimal('-50')
    assert x.balance == Decimal('50')

    x = txns[2]
    assert x.txn_id
    assert x.created_ts
    assert x.created_by == owner_user.id
    assert x.txn_type == 'MOVEOUT'
    assert x.txn_delta == Decimal('30')
    assert x.balance == Decimal('80')


    # check txn history for agent_1
    async with DBI() as db:
        txns = await db.get_agent_txns(member_id=agent_1.id)
    assert len(txns) == 4
    txns.sort(key=lambda x: x.txn_id)

    # check txn history for agent_2
    async with DBI() as db:
        txns = await db.get_agent_txns(member_id=agent_2.id)
    assert len(txns) == 2
    txns.sort(key=lambda x: x.txn_id)
