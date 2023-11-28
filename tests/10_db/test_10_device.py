import pytest

from ravvi_poker.db.dbi import DBI


@pytest.mark.asyncio
async def test_device(device):
    def check_row(row):
        assert row
        assert row.id == device.id
        assert row.uuid == device.uuid
        assert row.created_ts
        assert row.closed_ts is None

    async with DBI() as db:
        # by id
        row = await db.get_device(device.id)
        check_row(row)

        # by uuid
        row = await db.get_device(uuid=device.uuid)
        check_row(row)
