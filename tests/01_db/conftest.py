import asyncio
import pytest
import pytest_asyncio

from ravvi_poker.db.adbi import DBI
from helpers.services import Services


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
