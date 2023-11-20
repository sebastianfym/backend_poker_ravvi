import pytest

from ravvi_poker.db.adbi import DBI


@pytest.mark.asyncio
async def test_01_dbi_context():
    row1 = None
    row2 = None
    row3 = None
    async with DBI() as db:
        async with db.cursor() as cursor:
            await cursor.execute("INSERT INTO user_device (props) VALUES (NULL) RETURNING *")
            row1 = await cursor.fetchone()
        await db.dbi.rollback()
        async with db.cursor() as cursor:
            await cursor.execute("INSERT INTO user_device (props) VALUES (NULL) RETURNING *")
            row2 = await cursor.fetchone()
    assert row1 and row2

    try:
        async with DBI() as db:
            async with db.cursor() as cursor:
                await cursor.execute("INSERT INTO user_device (props) VALUES (NULL) RETURNING *")
                row3 = await cursor.fetchone()
            raise ValueError()
    except ValueError:
        pass

    async with DBI() as db:
        async with db.cursor() as cursor:
            await cursor.execute("SELECT * FROM user_device WHERE id=%s", (row1.id,))
            row = await cursor.fetchone()
            assert not row

            await cursor.execute("SELECT * FROM user_device WHERE id=%s", (row2.id,))
            row = await cursor.fetchone()
            assert row and row.id == row2.id

            await cursor.execute("SELECT * FROM user_device WHERE id=%s", (row3.id,))
            row = await cursor.fetchone()
            assert not row

