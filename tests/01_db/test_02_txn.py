import pytest

from ravvi_poker.db.txn import DBI, DBI_Txn


@pytest.mark.asyncio
async def test_txn_context():
    row1 = None
    row2 = None
    async with DBI() as db:
        async with DBI_Txn(db):
            row1 = await db.create_device() 
    assert row1

    try:
        async with DBI() as db:
            async with DBI_Txn(db):
                row2 = await db.create_device() 
                raise ValueError()
    except ValueError:
        pass

    async with DBI() as db:
        row = await db.get_device(row1.uuid)
        assert row and row.id == row1.id

        row = await db.get_device(row2.uuid)
        assert not row

