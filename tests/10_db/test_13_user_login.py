import logging
import pytest
import asyncio
import time

from ravvi_poker.db.adbi import DBI


@pytest.mark.dependency()
@pytest.mark.asyncio
async def test_login(login):
    def check_row(row):
        assert row
        assert row.id == login.id
        assert row.uuid == login.uuid
        assert row.user_id == login.user_id
        assert row.created_ts
        assert row.closed_ts is None

    async with DBI() as db:
        row = await db.get_login(login.id)
        check_row(row)

        row = await db.get_login(uuid=login.uuid)
        check_row(row)


@pytest.mark.dependency(depends=["test_login"])
@pytest.mark.asyncio
async def test_login_constrains(login):
    with pytest.raises(DBI.ForeignKeyViolation):
        async with DBI() as db:
            # invalid device
            await db.create_login(-1, login.user_id)
    with pytest.raises(DBI.ForeignKeyViolation):
        async with DBI() as db:
            # invalid device
            await db.create_login(login.device_id, -1)

@pytest.mark.dependency(depends=["test_login"])
@pytest.mark.asyncio
async def test_login_close(login):
    async with DBI() as db:
        x_login = await db.create_login(login.device_id, login.user_id)
        assert not x_login.closed_ts

    async with DBI() as db:
        await db.close_login(login.id)
    await asyncio.sleep(1)

    async with DBI() as db:
        login = await db.get_login(login.id)
        assert login.closed_ts
        x_login = await db.get_login(x_login.id)
        assert not x_login.closed_ts

    async with DBI() as db:
        await db.close_user(login.user_id)

    async with DBI() as db:
        login = await db.get_login(login.id)
        assert login.closed_ts
        x_login = await db.get_login(x_login.id)
        assert x_login.closed_ts
        assert login.closed_ts < x_login.closed_ts
