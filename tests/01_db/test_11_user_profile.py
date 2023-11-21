import pytest

from ravvi_poker.db.adbi import DBI

@pytest.mark.dependency()
@pytest.mark.asyncio
async def test_user(user):
    def check_row(row):
        assert row
        assert row.id == user.id
        assert row.uuid == user.uuid
        assert row.created_ts
        assert row.closed_ts is None

    async with DBI() as db:
        # get by id
        row = await db.get_user(user.id)
        check_row(row)

        # get by uuid
        row = await db.get_user(uuid=user.uuid)
        check_row(row)

@pytest.mark.dependency(depends=["test_user"])
@pytest.mark.asyncio
async def test_user_close(user):
    async with DBI() as db:
        row = await db.close_user(user.id)
        assert row
        assert row.closed_ts
