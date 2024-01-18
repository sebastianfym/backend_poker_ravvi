import asyncio

from ...db import DBI
from ..events import Message, Command
from .abs import ClientAbs
from .manager import ClientsManager

class ClientBase(ClientAbs):

    RESERVED_CMD_FIELDS = ['id','cmd_id','client_id']

    def __init__(self, manager: ClientsManager, client_id: int, user_id: int) -> None:
        super().__init__(client_id, user_id)
        self.manager = manager

    async def start(self):
        self.manager.clients[self.client_id] = self
        self.log.debug('started')

    async def on_shutdown(self):
        self.log.info("shutdown ...")
        async with DBI() as dbi:
            await dbi.close_client(self.client_id)

    async def send_cmd(self, cmd: dict):
        if isinstance(cmd, Command):
            cmd.update(client_id = self.client_id)
        elif isinstance(cmd, dict):
            kwargs = {k:v for k,v in cmd.items() if k not in self.RESERVED_CMD_FIELDS}
            cmd = Command(client_id = self.client_id, **kwargs)
        self.manager.send_cmd(self, cmd)
        self.log.info("send_cmd: %s", str(cmd))


class ClientQueue(ClientBase):

    def __init__(self, manager: ClientsManager, client_id: int, user_id: int) -> None:
        super().__init__(manager, client_id, user_id)
        self.msg_queue = asyncio.Queue()
        self.msg_task = None

    async def start(self):
        self.msg_task = asyncio.create_task(self.msg_queue_loop())
        super().start()

    async def shutdown(self):
        await self.msg_queue.put(None)

    async def wait_done(self):
        await self.msg_task

    async def handle_msg(self, msg: Message):
        await self.msg_queue.put(msg)

    async def msg_queue_loop(self):
        self.log.debug("msg_queue_loop: begin")
        while self.is_connected:
            # get next msg from queue
            msg: Message = await self.msg_queue.get()
            try:
                if not msg:
                    await self.on_shutdown()
                    break
                # handle message by client
                await self.on_msg(msg)
            except Exception as e:
                self.log.exception("msg: %s: %s", msg, e)
                break
            finally:
                self.msg_queue.task_done()
        self.log.debug("msg_queue_loop: end")

