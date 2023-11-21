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
    N = 1000
    async with DBI() as db:
        for _ in range(N):
            row = await db.create_login(login.device_id, login.user_id)
            assert not row.closed_ts

    async with DBI() as db:
        await db.close_login(login.id)
    await asyncio.sleep(1)

    async with DBI() as db:
        login = await db.get_login(login.id)
        assert login.closed_ts
        async with db.cursor() as cursor:
            await cursor.execute('SELECT * FROM user_login WHERE user_id=%s', (login.user_id,))
            for x in await cursor.fetchall():
                if x.id == login.id:
                    continue
                assert not x.closed_ts

    t0 = time.time()
    async with DBI() as db:
        await db.close_user(login.user_id)
    t1 = time.time()
    logging.info("close_user %s", t1-t0)

    async with DBI() as db:
        login = await db.get_login(login.id)
        assert login.closed_ts
        async with db.cursor() as cursor:
            await cursor.execute('SELECT * FROM user_login WHERE user_id=%s', (login.user_id,))
            for x in await cursor.fetchall():
                if x.id == login.id:
                    continue
                assert x.closed_ts
                assert login.closed_ts < x.closed_ts
