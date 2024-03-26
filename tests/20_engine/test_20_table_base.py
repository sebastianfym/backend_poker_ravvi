import pytest
import asyncio

import logging
logger = logging.getLogger(__name__)

from ravvi_poker.db import DBI
from ravvi_poker.engine.tables import Table, TablesManager

@pytest.mark.asyncio
async def test_table_start_stop_raw(table):

    kwargs = table._asdict()
    x_table = Table(**kwargs)
    await x_table.start()
    await x_table.wait_ready(timeout=5)
    await x_table.shutdown()
    await x_table.wait_done()


@pytest.mark.asyncio
async def test_table_start_stop_mgr():

    await DBI.pool_open()
    try:
        manager = TablesManager()

        # закрыть все существующие столы (невидимы для engine manager)
        async with DBI() as db:
            await db.dbi.execute('UPDATE table_profile SET engine_status=9, closed_ts=now_utc()')

        # запустить менеджер столов
        await manager.start()

        # создадим стол
        async with DBI() as db:
            row = await db.create_table(table_type="RG", table_seats=9, table_name="PUBLIC", game_type="NLH", game_subtype="REGULAR")
        await asyncio.sleep(5)

        x_table = manager.tables.get(row.id, None)
        assert x_table
        await asyncio.sleep(1)

        await x_table.shutdown()
        await asyncio.sleep(5)

        x_table = manager.tables.get(row.id, None)
        assert not x_table

        await asyncio.wait_for(manager.stop(), timeout=15)
        #assert not manager.tables
    finally:
        await manager.stop()
        await DBI.pool_close()
