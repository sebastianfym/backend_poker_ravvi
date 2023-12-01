import logging
import asyncio
import json
import contextlib

from .dbi import DBI, Notify
from .txn import DBI_Txn

logger = logging.getLogger(__name__)

class DBI_Listener:

    def __init__(self) -> None:
        super().__init__()
        self.log = logger
        self.task : asyncio.Task = None
        self.ready = asyncio.Event()
        self.channels = {}

    async def start(self):
        self.log.debug("start ...")
        self.task = asyncio.create_task(self.run())
        await self.ready.wait()
        self.log.info("started")

    async def stop(self):
        if not self.task:
            return
        self.log.debug("stop ...")
        if not self.task.done():
            self.task.cancel()
        with contextlib.suppress(asyncio.exceptions.CancelledError):
            await self.task
        self.task = None
        self.log.info("stopped")

    async def run(self):
        self.log.info("begin")
        # run until cancelled
        while True:
            try:
                async with DBI() as db:
                    async with DBI_Txn(db):
                        for key in self.channels:
                            self.log.info("listen: %s", key)
                            await db.listen(key)
                        await self.on_listen(db)
                    self.ready.set()
                    self.log.info('ready, process notifications ...')
                    async for msg in db.dbi.notifies():
                        async with DBI_Txn(db):
                            await self.on_notify(db, msg)
            except asyncio.CancelledError:
                self.log.info("cancelled")
                break
            except Exception as ex:
                self.log.exception("%s", ex)
            self.ready.clear()
        self.log.info("end")
    
    async def on_listen(self, db: DBI):
        pass

    async def on_notify(self, db: DBI, msg: Notify):
        self.log.debug("on_notify: %s", msg)
        handler = self.channels.get(msg.channel)
        if callable(handler):
            payload = json.loads(msg.payload) if msg.payload else {}
            await handler(db, **payload)
        else:
            await self.on_notify_default(db, msg)

    async def on_notify_default(self, db: DBI, msg: Notify):
        pass
