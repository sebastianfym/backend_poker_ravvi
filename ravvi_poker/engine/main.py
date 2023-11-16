import logging
import asyncio

from ..db.adbi import DBI
from .manager import Engine_Manager

logger = logging.getLogger(__name__)

async def main_task():
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
        task = asyncio.ensure_future(main_task())
        loop.run_until_complete(task)
    except KeyboardInterrupt:
        logger.info('SIGINT')
        if task:
            logger.info('cancelling tasks')
            task.cancel()
            loop.run_until_complete(task)
            task.exception()
    finally:
        loop.close()
        logger.info("run_async_loop: end")
        