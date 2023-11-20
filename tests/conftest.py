import asyncio
import pytest
import pytest_asyncio

from ravvi_poker.db.adbi import DBI

@pytest.fixture(autouse=True, scope="session")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()
