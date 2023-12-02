import asyncio

from ...db import DBI
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

    async def shutdown(self):
        self.log.info("shutdown ...")
        async with DBI() as dbi:
            await dbi.close_client(self.client_id)

    async def wait_done(self):
        self.log.info("wait_done")
        pass

    async def handle_msg(self, msg: Message):
        await self.on_msg(msg)

    async def on_msg(self, msg: Message):
        pass

    RESERVED_CMD_FIELDS = ['id','cmd_id','client_id']

    async def send_cmd(self, cmd: dict):
        if isinstance(cmd, Command):
            cmd.update(client_id = self.client_id)
        elif isinstance(cmd, dict):
            kwargs = {k:v for k,v in cmd if k not in self.RESERVED_CMD_FIELDS}
            cmd = Command(client_id = self.client_id, **kwargs)
        async with DBI(log=self.log) as db:
            await db.create_table_cmd(client_id=self.client_id, table_id=cmd.table_id, cmd_type=cmd.cmd_type, props=cmd.props)
        self.log.info("send_cmd: %s", str(cmd))


class ClientQueue(ClientBase):

    def __init__(self, client_id, user_id) -> None:
        super().__init__(client_id, user_id)
        self.msg_queue = asyncio.Queue()
        self.msg_task = None

    async def start(self):
        self.msg_task = asyncio.create_task(self.msg_queue_loop())

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
                    await super().shutdown()
                    break
                # handle message by client
                await self.on_msg(msg)
            except Exception as e:
                self.log.exception("msg: %s: %s", msg, e)
                break
            finally:
                self.msg_queue.task_done()
        self.log.debug("msg_queue_loop: end")

