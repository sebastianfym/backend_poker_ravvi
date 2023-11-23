import pytest
import asyncio
import pytest_asyncio

from ravvi_poker.db.adbi import DBI

@pytest.fixture(autouse=True, scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(autouse=True, scope="package")
async def dbi_pool():
    await DBI.pool_open()
    yield
    await DBI.pool_close()


@pytest_asyncio.fixture
async def device():
    async with DBI() as db:
        row = await db.create_device()
        assert row
        assert row.id
        assert row.uuid
        assert row.created_ts
        assert row.closed_ts is None
    yield row


@pytest_asyncio.fixture
async def user():
    async with DBI() as db:
        row = await db.create_user()
        assert row
    yield row


@pytest_asyncio.fixture
async def users_10():
    rows = []
    for _ in range(10):
        async with DBI() as db:
            row = await db.create_user()
            rows.append(row)
    yield rows


@pytest_asyncio.fixture
async def login(device, user):
    async with DBI() as db:
        row = await db.create_login(device.id, user.id)
        assert row
    yield row


@pytest_asyncio.fixture
async def session(login):
    async with DBI() as db:
        row = await db.create_session(login.id)
        assert row
    yield row


@pytest_asyncio.fixture
async def client(session):
    async with DBI() as db:
        row = await db.create_client(session.id)
        assert row
    yield row

@pytest_asyncio.fixture()
async def table():
    async with DBI() as db:
        row = await db.create_table(
            table_type="REGULAR", table_seats=9, table_name="PUBLIC", game_type="NLH", game_subtype="DEFAULT"
        )
        assert row
    yield row
