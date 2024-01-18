from ...logging import ObjectLoggerAdapter, getLogger
from ..events import Command, Message

logger = getLogger(__name__)

class ClientAbs:

    def __init__(self, client_id: int, user_id: int) -> None:
        self.log = ObjectLoggerAdapter(logger, lambda: f"{self.client_id}({self.user_id})")
        self.client_id = client_id
        self.user_id = user_id
        self.tables = set()

    @property
    def is_connected(self):
        return True
    
    async def start(self):
        pass

    async def shutdown(self):
        await self.on_shutdown()

    async def wait_done(self):
        self.log.info("wait_done")

    async def handle_msg(self, msg: Message):
        await self.on_msg(msg)

    async def on_msg(self, msg: Message):
        pass

    async def on_shutdown(self):
        pass
   
   
ClientsMap = dict[int,ClientAbs]
