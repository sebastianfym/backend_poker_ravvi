import pytest
import pytest_asyncio

from ravvi_poker.db.adbi import DBI

@pytest_asyncio.fixture(scope="module")
async def table():
    async with DBI() as db:
        row = await db.create_table(
            table_type="REGULAR", table_seats=9, table_name="PUBLIC", game_type="NLH", game_subtype="DEFAULT"
        )
        assert row
        return row


@pytest.mark.dependency()
@pytest.mark.asyncio
async def test_01_table(table):
    assert table
    async with DBI() as db:
        row = await db.get_table(table.id)
        assert row
        assert row.id == table.id
        assert row.table_name == "PUBLIC"
        assert row.table_type == "REGULAR"
        assert row.table_seats == 9
        assert row.game_type == "NLH"
        assert row.game_subtype == "DEFAULT"
        assert row.props == {}

        rows = await db.get_open_tables()
        assert rows

@pytest.mark.dependency(depends=["test_01_table"])
@pytest.mark.asyncio
async def test_02_table_users(table, users):
    assert table
    async with DBI() as db:
        for user in users:
            row = await db.create_table_user(table.id, user.id)
            assert row
            assert row.table_id == table.id
            assert row.user_id == user.id
            assert row.last_game_id is None

@pytest.mark.dependency(depends=["test_02_table_users"])
@pytest.mark.asyncio
async def test_03_table_close(table):
    assert table
    async with DBI() as db:
        row = await db.close_table(table.id)
        assert row
        assert row.closed_ts

    async with DBI() as db:
        row = await db.get_table(table.id)
        assert row
        assert row.closed_ts