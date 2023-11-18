import logging
import asyncio
import json

from ..logging import Logger_MixIn
from .adbi import DBI, Notify

class DBI_Listener(Logger_MixIn):

    logger = logging.getLogger(__name__)

    def __init__(self) -> None:
        super().__init__()
        self.task : asyncio.Task = None
        self.channels = {}

    async def start(self):
        self.log_info("start")
        self.task = asyncio.create_task(self.run())
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
    
    async def process_events(self):
        async with DBI() as db:
            async with db.txn():
                for key in self.channels:
                    await db.execute(f"LISTEN {key}")
                await self.on_listen_begin(db)
            async for msg in db.dbi.notifies():
                async with db.txn():
                    await self.on_notification(db, msg)

    async def on_listen_begin(self, db):
        pass

    async def on_notification(self, db: DBI, msg: Notify):
        handler = self.channels.get(msg.channel)
        if not callable(handler):
            return
        payload = json.loads(msg.payload) if msg.payload else {}
        await handler(db, **payload)

