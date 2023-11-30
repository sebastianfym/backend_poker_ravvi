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
        self.task_stop = False
        self.ready = asyncio.Event()
        self.channels = {}

    async def start(self):
        self.log.debug("start ...")
        self.task_stop = False
        self.task = asyncio.create_task(self.run())
        await self.ready.wait()
        self.log.info("started")

    async def stop(self):
        self.log.debug("stop ...")
        self.task_stop = True
        if self.task:
            if not self.task.done():
                self.task.cancel()
            with contextlib.suppress(asyncio.exceptions.CancelledError):
                await self.task
        self.task = None
        self.log.info("stopped")

    async def run(self):
        self.log.info("begin")
        while not self.task_stop:
            try:
                await self.process_events()
            except Exception as ex:
                self.log.exception("exception: %s", str(ex))
        self.ready.clear()
        self.log.info("end")
    
    async def process_events(self):
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
                    try:
                        await self.on_notify(db, msg)
                    except asyncio.CancelledError:
                        self.log.info("cancelled")
                        self.task_stop = True
                        break
                    except Exception as e:
                        self.log.exception("%s", e)
            async with DBI_Txn(db):
                for key in self.channels:
                    self.log.info("unlisten: %s", key)
                    await db.unlisten(key)

    async def on_listen(self, db: DBI):
        pass

    async def on_notify(self, db: DBI, msg: Notify):
        self.log.info("on_notify: %s", msg)
        handler = self.channels.get(msg.channel)
        if callable(handler):
            payload = json.loads(msg.payload) if msg.payload else {}
            await handler(db, **payload)
        else:
            await self.on_notify_default(db, msg)

    async def on_notify_default(self, db: DBI, msg: Notify):
        pass
