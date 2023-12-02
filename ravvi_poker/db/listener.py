import logging
import asyncio
import json
import contextlib

from .dbi import DBI, Notify

logger = logging.getLogger(__name__)

class DBI_Listener:

    def __init__(self, *, log=None) -> None:
        super().__init__()
        self.log = log or logger
        self.task : asyncio.Task = None
        self.ready = asyncio.Event()
        self.channels = {}
        self.pg_backend_pid = None

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
                async with DBI(log=self.log, use_pool=False) as dbi:
                    async with dbi.transaction():
                        self.pg_backend_pid = await dbi.get_pg_backend_pid()
                        for key in self.channels:
                            self.log.info("listen: %s", key)
                            await dbi.listen(key)
                    await self.on_listen(self.pg_backend_pid)
                    self.ready.set()
                    self.log.info('ready, process notifications ...')
                    async for msg in dbi.dbi.notifies():
                        #await dbi.commit()
                        await self.on_notify(msg)
            except asyncio.CancelledError:
                self.log.info("cancelled")
                break
            except Exception as ex:
                self.log.exception("%s", ex)
            finally:
                self.ready.clear()
        self.log.info("end")
    
    async def on_listen(self, backend_id: int):
        pass

    async def on_notify(self, msg: Notify):
        self.log.debug("on_notify: %s", msg)
        handler = self.channels.get(msg.channel)
        if callable(handler):
            payload = json.loads(msg.payload) if msg.payload else {}
            await handler(**payload)
