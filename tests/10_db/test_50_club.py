import logging
import pytest

from ravvi_poker.db.adbi import DBI

log = logging.getLogger(__name__)

@pytest.mark.dependency()
@pytest.mark.asyncio
async def test_club_create(user):
    async with DBI() as db:
        row = await db.create_club(user_id=user.id, name='TEST', description='test', image_id=None)
    assert row
    assert not row.closed_ts

    club_id = row.id
    async with DBI() as db:
        club = await db.get_club(club_id)
        members = await db.get_club_members(club_id)
    assert club.id == club_id
    assert club.name == 'TEST'
    assert club.description == 'test'
    assert club.image_id is None

    assert members and len(members)==1
    owner = members[0]
    assert owner.user_id == user.id
    assert owner.user_role == 'OWNER'
    assert owner.created_ts
    assert owner.approved_ts
    assert not owner.closed_ts

    async with DBI() as db:
        club = await db.update_club(club_id, name='NAME', image_id=11)
    assert club.id == club_id
    assert club.name == 'NAME'
    assert club.description == 'test'
    assert club.image_id==11

@pytest.mark.dependency(depands=['test_club_create'])
@pytest.mark.asyncio
async def test_club_member(club_and_owner, user):
    club, owner = club_and_owner

    #log.info('create club %s member %s', club.id, user.id)
    async with DBI() as db:
        member = await db.create_club_member(club.id, user.id, 'user comment')
    assert member
    assert member.club_id == club.id
    assert member.user_id == user.id
    assert member.user_comment == 'user comment'
    assert member.user_role == 'PLAYER'
    assert member.created_ts
    assert member.approved_ts is None
    assert member.approved_by is None
    assert member.club_comment is None
    assert member.closed_ts is None

    async with DBI() as db:
        member = await db.approve_club_member(member.id, owner.id, 'club comment')
    assert member
    assert member.club_id == club.id
    assert member.user_id == user.id
    assert member.user_comment == 'user comment'
    assert member.user_role == 'PLAYER'
    assert member.created_ts
    assert member.approved_ts
    assert member.approved_by == owner.id
    assert member.club_comment == 'club comment'
    assert member.closed_ts is None



