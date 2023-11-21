import pytest

from ravvi_poker.db.adbi import DBI


@pytest.mark.asyncio
async def test_01_users(users):
    assert len(users) == 10
    async with DBI() as db:
        for u in users:
            row = await db.get_user(u.id)
            assert row
            assert u.id == row.id
            assert u.created_ts
