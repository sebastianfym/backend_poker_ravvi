import pytest

from ravvi_poker.db.dbi import DBI

@pytest.mark.asyncio
async def test_dbi_app_name():
    async with DBI() as db:
        async with db.cursor() as cursor:
            await cursor.execute("SELECT application_name FROM pg_stat_activity WHERE pid=pg_backend_pid()")
            row = await cursor.fetchone()
    assert row.application_name == DBI.APPLICATION_NAME


@pytest.mark.asyncio
async def test_dbi_context():
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
        row = await db.get_device(row1.id)
        assert not row

        row = await db.get_device(row2.id)
        assert row and row.id == row2.id

        row = await db.get_device(row3.id)
        assert not row


@pytest.mark.asyncio
async def test_dbi_use_id_or_uuid():
    db = DBI()
    with pytest.raises(ValueError):
        key, value = db.use_id_or_uuid(None, None)

    key, value = db.use_id_or_uuid(111, None)
    assert key == "id"
    assert value == 111

    key, value = db.use_id_or_uuid(111, "UUID-111")
    assert key == "id"
    assert value == 111

    key, value = db.use_id_or_uuid(None, "UUID-111")
    assert key == "uuid"
    assert value == "UUID-111"
