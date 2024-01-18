import pytest
import pytest_asyncio

from ravvi_poker.db.dbi import DBI


@pytest.mark.dependency()
@pytest.mark.asyncio
async def test_table(table):
    assert table
    async with DBI() as db:
        row = await db.get_table(table.id)
        assert row
        assert row.id == table.id
        assert row.table_name == "PUBLIC"
        assert row.table_type == "RG"
        assert row.table_seats == 9
        assert row.game_type == "NLH"
        assert row.game_subtype == "REGULAR"
        assert row.props == {}

        rows = await db.get_open_tables()
        assert rows


@pytest.mark.dependency(depends=["test_table"])
@pytest.mark.asyncio
async def test_table_close(table):
    async with DBI() as db:
        row = await db.close_table(table.id)
        assert row
        assert row.closed_ts

    async with DBI() as db:
        row = await db.get_table(table.id)
        assert row
        assert row.closed_ts
