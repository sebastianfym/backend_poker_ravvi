import logging
import pytest
from decimal import Decimal

from ravvi_poker.db.dbi import DBI

from helpers.x_utils import check_timestamp_threshold

log = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_chips_player(club_and_owner, users_10):
    club, owner_user = club_and_owner
    user_1, user_2 = users_10[:2]
    async with DBI() as db:
        club = await db.get_club(club.id)
        owner_member = await db.find_member(club_id=club.id, user_id=owner_user.id)
        agent_1 = await db.create_club_member(club_id=club.id, user_id=user_1.id)
        await db.approve_club_member(agent_1.id, owner_user.id, user_role='A', club_comment=None, nickname=None)
        player_2 = await db.create_club_member(club_id=club.id, user_id=user_2.id)
        await db.approve_club_member(player_2.id, owner_user.id, user_role='P', club_comment=None, nickname=None)

    assert owner_member
    assert club.club_balance == 0
    assert owner_member.balance == 0
    assert agent_1.balance == 0
    assert agent_1.balance_shared == 0
    assert player_2.balance == 0
    assert player_2.balance_shared == 0

    # add 1000 to club
    async with DBI() as db:
        txn = await db.create_txn_CHIPSIN(txn_user_id=owner_user.id, club_id=club.id, txn_value=1000.0001)

    # give some chips to agent
    async with DBI() as db:
        await db.create_txn_MOVEIN(txn_user_id=owner_user.id, club_id=club.id, member_id=agent_1.id, ref_member_id=None, txn_value=100)

    # give some chips to player
    async with DBI() as db:
        await db.create_txn_CASHIN(txn_user_id=owner_user.id, club_id=club.id, member_id=player_2.id, ref_member_id=None, txn_value=200)

    # give some chips to player from agent
    async with DBI() as db:
        await db.create_txn_CASHIN(txn_user_id=owner_user.id, club_id=club.id, member_id=player_2.id, ref_member_id=agent_1.id, txn_value=50)

    async with DBI() as db:
        club = await db.get_club(club.id)
        agent_1 = await db.get_club_member(agent_1.id)
        player_2 = await db.get_club_member(player_2.id)

    assert club.club_balance == Decimal('700')
    assert owner_member.balance == 0
    assert agent_1.balance == 0
    assert agent_1.balance_shared == Decimal('50')
    assert player_2.balance == Decimal('250')
    assert player_2.balance_shared == 0

    # take some chips from player
    async with DBI() as db:
        await db.create_txn_CASHOUT(txn_user_id=owner_user.id, club_id=club.id, member_id=player_2.id, ref_member_id=None, txn_value=25)

    # take some chips from player by agent
    async with DBI() as db:
        await db.create_txn_CASHOUT(txn_user_id=owner_user.id, club_id=club.id, member_id=player_2.id, ref_member_id=agent_1.id, txn_value=100)

    async with DBI() as db:
        club = await db.get_club(club.id)
        agent_1 = await db.get_club_member(agent_1.id)
        player_2 = await db.get_club_member(player_2.id)

    assert club.club_balance == Decimal('725')
    assert owner_member.balance == 0
    assert agent_1.balance == 0
    assert agent_1.balance_shared == Decimal('150')
    assert player_2.balance == Decimal('125')
    assert player_2.balance_shared == 0

    # check txn history for agent_1
    async with DBI() as db:
        txns = await db.get_agent_txns(member_id=agent_1.id)
    assert len(txns) == 3
    txns.sort(key=lambda x: x.txn_id)

    # check txn history for player_2
    async with DBI() as db:
        txns = await db.get_player_txns(member_id=player_2.id)
    assert len(txns) == 4
    txns.sort(key=lambda x: x.txn_id)
