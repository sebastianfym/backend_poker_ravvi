import pytest

from ravvi_poker.db.dbi import DBI
from helpers.x_listener import X_DBI_Listener


@pytest.mark.dependency()
@pytest.mark.asyncio
async def test_client(client):
    def check_row(row):
        assert row
        assert row.id == client.id
        assert row.session_id == client.session_id
        assert row.created_ts
        assert row.closed_ts is None

    async with DBI() as db:
        row = await db.get_client(client.id)
        check_row(row)


@pytest.mark.dependency(depends=["test_client"])
@pytest.mark.asyncio
async def test_client_constrains(session):
    with pytest.raises(DBI.ForeignKeyViolation):
        async with DBI() as db:
            # invalid login
            await db.create_client(-1)


@pytest.mark.dependency(depends=["test_client_constrains"])
@pytest.mark.asyncio
async def test_client_info(client):
    def check_row(row):
        assert row

    async with DBI() as db:
        row = await db.get_client_info(client.id)
        check_row(row)


@pytest.mark.dependency(depends=["test_client"])
@pytest.mark.asyncio
async def test_client_close(client):
    async with DBI() as db:
        x_client = await db.create_client(client.session_id)
        assert not x_client.closed_ts

    async with X_DBI_Listener("user_client_closed") as x:
        async with DBI() as db:
            client = await db.close_client(client.id)
            assert client
            assert client.closed_ts
    assert x.expected and len(x.expected) == 1
    payload = x.expected[0]
    assert payload["client_id"] == client.id

    async with DBI() as db:
        client = await db.get_client(client.id)
        assert client.closed_ts
        x_client = await db.get_client(x_client.id)
        assert not x_client.closed_ts

    async with X_DBI_Listener("user_client_closed") as x:
        async with DBI() as db:
            await db.close_session(client.session_id)
    assert x.expected and len(x.expected) == 1
    payload = x.expected[0]
    assert payload["client_id"] == x_client.id

    async with DBI() as db:
        client = await db.get_client(client.id)
        assert client.closed_ts
        x_client = await db.get_client(x_client.id)
        assert x_client.closed_ts
        assert client.closed_ts < x_client.closed_ts
