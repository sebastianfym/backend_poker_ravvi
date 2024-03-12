import asyncio
import pytest
import pytest_asyncio

from ravvi_poker.db.dbi import DBI

DBI.POOL_LIMIT = 5

async def run_db_query(value):
    async with DBI() as db:
        async with db.cursor() as cursor:
            await cursor.execute("SELECT %s value", (value,))
            row = await cursor.fetchone()
    return row.value

@pytest.mark.asyncio
async def test_dbi_stress_workload():
    # run requests w/o dbi pool
    values = range(1000)
    requests = [run_db_query(x) for x in values]
    results = await asyncio.gather(*requests, return_exceptions=True)
    # check result
    fail_counter = 0
    for x, y in zip(values,results):
        if x != y:
            fail_counter += 1
    # make sure some failed
    assert fail_counter


@pytest.mark.asyncio
async def test_dbi_stress_with_pool(dbi_pool):
    # do again with dbi pool
    values = range(1000)
    requests = [run_db_query(x) for x in values]
    results = await asyncio.gather(*requests, return_exceptions=True)
    # check result
    for x, y in zip(values,results):
        assert x == y
    # all requests should be executed w/o errors
