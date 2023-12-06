import logging
import asyncio

from ..db import DBI
from .tables.manager import TablesManager

logger = logging.getLogger(__name__)


async def start_engine():
    #await DBI.pool_open()
    engine = TablesManager()
    await engine.start()
    return engine


async def stop_engine(engine):
    await engine.stop()
    #await DBI.pool_close()


async def master_task():
    engine = await start_engine()
    try:
        while True:
            await asyncio.sleep(10)
    except asyncio.CancelledError:
        logger.info("master task cancelled")
    finally:
        await stop_engine(engine)


def run_async_loop():
    logger.info("run_async_loop: begin")
    loop = asyncio.get_event_loop()
    master = asyncio.ensure_future(master_task())

    def cancel_master():
        if not master:
            return
        logger.info("cancelling tasks")
        master.cancel()
        loop.run_until_complete(master)
        master.exception()

    try:
        loop.run_until_complete(master)
    except SystemExit:
        logger.info("SIGTERM")
        cancel_master()
    except KeyboardInterrupt:
        logger.info("SIGINT")
        cancel_master()
    finally:
        loop.close()
        logger.info("run_async_loop: end")
