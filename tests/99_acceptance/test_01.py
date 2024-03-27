import pytest

pytestmark = pytest.mark.skip()

import logging
import asyncio
import pytest

from ravvi_poker.api.app import app as api_app

from helpers.client import Client, Message

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_01_01():

    c1 = Client()
    await c1.register()
    
    await c1.ws_connect()
    async with c1.ws_response(Message.Type.TABLE_INFO, 3) as t:
        await c1.cmd_TABLE_JOIN(table_id=11, take_seat=True)
    logger.info('r_time: %.3fms', t.time_ms)
    
    await asyncio.sleep(2)
    assert c1.ws_log

    await c1.ws_close()
