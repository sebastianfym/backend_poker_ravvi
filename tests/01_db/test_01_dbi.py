import pytest

from ravvi_poker.db.adbi import DBI


@pytest.mark.asyncio
async def test_01_dbi_context():
    row1 = None
    row2 = None
    row3 = None
    async with DBI() as db:
        row1 = await db.create_device()
        await db.dbi.rollback()
        row2 = await db.create_device()
    assert row1 and row2

    try:
        async with DBI() as db:
            row3 = await db.create_device()
            raise ValueError()
    except ValueError:
        pass

    async with DBI() as db:
        row = await db.get_device(row1.uuid)
        assert not row

        row = await db.get_device(row2.uuid)
        assert row and row.id == row2.id

        row = await db.get_device(row3.uuid)
        assert not row
