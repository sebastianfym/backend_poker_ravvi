import logging
import asyncio

from ..db.adbi import DBI
from .manager import Engine_Manager

logger = logging.getLogger(__name__)

async def master_task():
    await DBI.pool_open()
    engine = Engine_Manager()
    await engine.start()
    try:
        while True:
            await asyncio.sleep(10)
    except asyncio.CancelledError:
        logger.info('task cancelled')
    finally:
        await engine.stop()
        await DBI.pool_close()

def run_async_loop():
    logger.info("run_async_loop: begin")
    loop = asyncio.get_event_loop()
    try:
        master = asyncio.ensure_future(master_task())
        loop.run_until_complete(master)
    except KeyboardInterrupt:
        logger.info('SIGINT')
        if master:
            logger.info('cancelling tasks')
            master.cancel()
            loop.run_until_complete(master)
            master.exception()
    finally:
        loop.close()
        logger.info("run_async_loop: end")
        