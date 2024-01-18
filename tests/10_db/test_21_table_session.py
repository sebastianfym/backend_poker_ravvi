import pytest
import pytest_asyncio

from ravvi_poker.db.dbi import DBI


@pytest.mark.asyncio
async def test_table_session_register(table, user):
    async with DBI() as db:
        account = await db.find_account(user_id=user.id, club_id=0)
        row = await db.register_table_session(table.id, account.id)
    assert row
    assert row.table_id == table.id
    assert row.account_id == account.id
    assert not row.opened_ts
    assert not row.closed_ts

    async with DBI() as db:
        row2 = await db.register_table_session(table.id, account.id)
    assert row2
    assert row2.id == row.id
    assert not row.opened_ts
    assert not row.closed_ts

    async with DBI() as db:
        row2 = await db.close_table_session(row.id)
    assert row2
    assert row2.id == row.id
    assert not row2.opened_ts
    assert row2.closed_ts

    async with DBI() as db:
        row3 = await db.register_table_session(table.id, account.id)
    assert row3
    assert row3.id != row.id
    assert row3.table_id == table.id
    assert row3.account_id == account.id
    assert not row3.opened_ts
    assert not row3.closed_ts

    async with DBI() as db:
        row4 = await db.open_table_session(row3.id)
    assert row4
    assert row4.id == row3.id
    assert row4.opened_ts
    assert not row4.closed_ts

    async with DBI() as db:
        row4 = await db.close_table_session(row3.id)
    assert row4
    assert row4.id == row3.id
    assert row4.opened_ts
    assert row4.closed_ts


@pytest.mark.asyncio
async def test_table_session_reuse(table, user):
    async with DBI() as db:
        account = await db.find_account(user_id=user.id, club_id=0)
        row = await db.reuse_table_session(table.id, account.id)
    assert row
    assert row.table_id == table.id
    assert row.account_id == account.id
    assert row.opened_ts
    assert not row.closed_ts

    async with DBI() as db:
        row2 = await db.reuse_table_session(table.id, account.id)
    assert row2
    assert row2.id == row.id
    assert row2.table_id == table.id
    assert row2.account_id == account.id
    assert row2.opened_ts
    assert not row.closed_ts

    async with DBI() as db:
        await db.close_table_session(row.id)

    async with DBI() as db:
        row3 = await db.reuse_table_session(table.id, account.id)
    assert row3
    assert row3.id == row.id
    assert row3.table_id == table.id
    assert row3.account_id == account.id
    assert row3.opened_ts
    assert not row.closed_ts

    async with DBI() as db:
        await db.close_table_session(row.id)
        sql = "UPDATE table_session SET opened_ts=opened_ts-interval '2 hour', closed_ts=closed_ts-interval '2 hour' "
        sql += " WHERE id=%s"
        await db.dbi.execute(sql, (row.id,))

    async with DBI() as db:
        row4 = await db.reuse_table_session(table.id, account.id)
    assert row4
    assert row4.id != row.id
    assert row4.table_id == table.id
    assert row4.account_id == account.id
    assert row4.opened_ts
    assert not row.closed_ts
