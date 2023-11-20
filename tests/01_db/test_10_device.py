import pytest

from ravvi_poker.db.adbi import DBI

@pytest.mark.asyncio
async def test_01_devices(devices):
    assert len(devices) == 10
    async with DBI() as db:
        for d in devices:
            row = await db.get_device(d.uuid)
            assert row
            assert d.id == row.id
            assert d.uuid
            assert d.created_ts
            assert d.closed_ts is None

