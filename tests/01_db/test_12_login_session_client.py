import pytest

from ravvi_poker.db.adbi import DBI


@pytest.mark.asyncio
async def test_01_login_and_session_and_client():
    async with DBI() as db:
        device = await db.create_device()
        assert device
        user = await db.create_user()
        assert user
        login = await db.create_login(device.id, user.id)
        assert login
        session = await db.create_session(login.id)
        assert session
        client = await db.create_client(session.id)
        assert client

    async with DBI() as db:
        row = await db.get_login(uuid=login.uuid)
        assert row
        assert row.device_id == device.id
        assert row.user_id == user.id

        row = await db.get_session_info(uuid=session.uuid)
        assert row

        row = await db.get_client_info(client.id)
        assert row
        assert row.user_id == user.id

    async with DBI() as db:
        row = await db.close_client(client.id)
        assert row
        assert row.closed_ts
        row = await db.close_session(session.id)
        assert row
        assert row.closed_ts
        row = await db.close_login(login.id)
        assert row
        assert row.closed_ts

    async with DBI() as db:
        row = await db.get_client_info(client.id)
        assert row
        assert row.user_id == user.id
        assert row.closed_ts

        row = await db.get_login(uuid=login.uuid)
        assert row
        assert row.closed_ts

        row = await db.get_session_info(uuid=session.uuid)
        assert row
        assert row.session_closed_ts
        assert row.login_closed_ts
