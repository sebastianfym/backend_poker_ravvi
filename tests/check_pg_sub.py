import logging
import asyncio
from datetime import datetime, timedelta
from ravvi_poker.db.adbi import DBI
from ravvi_poker.db.listener import DBI_Listener

class TestManager(DBI_Listener):

    logger = logging.getLogger(__name__)

    def __init__(self) -> None:
        super().__init__()
        self.channels = {
            'poker_event_cmd': self.handler
        }

#    async def on_notification(self, db, msg):
#        print(msg)

    async def handler(self, db, **kwargs):
        print(kwargs)

async def main_task():
    await DBI.pool_open()
    manager = TestManager()
    await manager.start()
    try:
        await asyncio.sleep(10)
    except asyncio.CancelledError:
        print('task cancelled')
    finally:
        await manager.stop()
        await DBI.pool_close()
    return 'TEST'

def main():
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    logging.basicConfig(level=logging.INFO)
    try:
        task = asyncio.ensure_future(main_task())
        result = loop.run_until_complete(task)
        print('Result: {}'.format(result))
    except KeyboardInterrupt:
        print('got SIGINT')
        if task:
            print('cancelling tasks')
            task.cancel()
            result = loop.run_until_complete(task)
            task.exception()
    finally:
        loop.close()
        
if __name__=='__main__':
    main()