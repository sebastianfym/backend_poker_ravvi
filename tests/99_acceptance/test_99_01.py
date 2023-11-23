import pytest
pytestmark = pytest. mark. skip()

import logging
import asyncio
import pytest

from helpers.services import Services
from helpers.client import Client, Event

logger = logging.getLogger(__name__)


@pytest.mark.asyncio
async def test_99_01_01():
    c1 = Client()
    await c1.register()
    
    await c1.ws_connect()
    async with c1.ws_response(Event.TABLE_INFO) as t:
        await c1.cmd_TABLE_JOIN(table_id=11, take_seat=True)
    logger.info('r_time: %.3fms', t.time_ms)
    
    await asyncio.sleep(1)
    assert c1.ws_log

    await c1.ws_close()

if __name__=='__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    import os
    start_from = os.path.dirname(__file__)
    pytest.main([start_from])
#    import asyncio
#    asyncio.run(test_99_01_01())