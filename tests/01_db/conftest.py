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


@pytest_asyncio.fixture(scope="package")
async def devices():
    rows = []
    for _ in range(10):
        async with DBI() as db:
            row = await db.create_device()
            rows.append(row)
    yield rows


@pytest_asyncio.fixture(scope="package")
async def users():
    rows = []
    for _ in range(10):
        async with DBI() as db:
            row = await db.create_user()
            rows.append(row)
    yield rows


@pytest_asyncio.fixture
async def client():
    async with DBI() as db:
        device = await db.create_device()
        user = await db.create_user()
        login = await db.create_login(device.id, user.id)
        session = await db.create_session(login.id)
        client = await db.create_client(session.id)
    yield client
