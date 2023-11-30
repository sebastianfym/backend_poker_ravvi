import asyncio
from contextlib import suppress

from ...logging import ObjectLoggerAdapter, getLogger
from ..events import Message, Command

log = getLogger(__name__)

class ClientBase:

    def __init__(self, client_id, user_id) -> None:
        self.client_id = client_id
        self.user_id = user_id
        self.manager = None
        self.tables = set()
        self.log = ObjectLoggerAdapter(log, lambda: f"{self.client_id}({self.user_id})")

    @property
    def is_connected(self):
        return True
    
    async def start(self):
        pass

    async def stop(self):
        pass

    async def handle_msg(self, msg: Message):
        await self.on_msg(msg)

    async def on_msg(self, msg: Message):
        pass

    async def send_cmd(self, cmd: dict):
        self.log.info("cmd: %s", cmd)
        await self.manager.send_cmd(self, cmd)


class ClientQueue(ClientBase):

    def __init__(self, client_id, user_id) -> None:
        super().__init__(client_id, user_id)
        self.msg_queue = asyncio.Queue()
        self.msg_task = None

    async def start(self):
        self.msg_task = asyncio.create_task(self.msg_queue_loop())

    async def stop(self):
        if not self.msg_task.done():
            self.msg_task.cancel()
        with suppress(asyncio.exceptions.CancelledError):
            await self.msg_task

    async def handle_msg(self, msg: Message):
        await self.msg_queue.put(msg)

    async def msg_queue_loop(self):
        self.log.debug("msg_queue_loop: begin")
        while self.is_connected:
            try:
                # get next msg from queue
                msg: Message = await self.msg_queue.get()
                try:
                    # handle message by client
                    await self.on_msg(msg)
                except Exception as e:
                    self.log.exception("msg: %s: %s", msg, e)
                    break
                finally:
                    self.msg_queue.task_done()
            except asyncio.CancelledError:
                self.log.info("msg_queue_loop: cancelled")
                break
        self.log.debug("msg_queue_loop: end")

