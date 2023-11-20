import logging
import asyncio
import json

from ..logging import Logger_MixIn
from .adbi import DBI, Notify
from .txn import DBI_Txn

class DBI_Listener(Logger_MixIn):

    logger = logging.getLogger(__name__)

    def __init__(self) -> None:
        super().__init__()
        self.task : asyncio.Task = None
        self.ready = asyncio.Event()
        self.channels = {}

    async def start(self):
        self.log_info("start")
        self.task = asyncio.create_task(self.run())
        await self.ready.wait()
        self.log_info("started")

    async def stop(self):
        self.log_info("stop")
        if self.task:
            if not self.task.done():
                self.task.cancel()
        await self.task
        self.task = None
        self.log_info("stopped")

    async def run(self):
        while True:
            try:
                await self.process_events()
            except asyncio.CancelledError:
                self.log_info("cancelled")
                break
            except Exception as ex:
                self.log_exception("exception: %s", str(ex))
                await asyncio.sleep(5)
            finally:
                self.ready.clear()
    
    async def process_events(self):
        async with DBI() as db:
            async with DBI_Txn(db):
                for key in self.channels:
                    self.log_info("listen: %s", key)
                    await db.listen(key)
                await self.on_listen(db)
            self.ready.set()
            self.log_info('ready, process notifications ...')
            async for msg in db.dbi.notifies():
                async with DBI_Txn(db):
                    try:
                        await self.on_notify(db, msg)
                    except Exception as e:
                        self.log_exception("%s", e)

    async def on_listen(self, db: DBI):
        pass

    async def on_notify(self, db: DBI, msg: Notify):
        handler = self.channels.get(msg.channel)
        if callable(handler):
            payload = json.loads(msg.payload) if msg.payload else {}
            await handler(db, **payload)
        else:
            await self.on_notify_default(db, msg)

    async def on_notify_default(self, db: DBI, msg: Notify):
        pass
