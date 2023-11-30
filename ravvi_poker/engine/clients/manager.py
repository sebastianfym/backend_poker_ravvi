import logging
import asyncio

from ...db import DBI, DBI_Listener
from ..events import Command, Message
from .base import ClientBase

logger = logging.getLogger(__name__)

class ClientsManager:

    def __init__(self):
        self.log = logger
        self.clients = {}
        self.table_subscribers = {}
        self.last_event_id = None
        self.listener = DBI_Listener()
        self.listener.log = self.log
        self.listener.channels = {
            "table_msg": self.on_table_msg
        }

    async def start(self):
        await self.listener.start()

    async def stop(self):
        await self.listener.stop()

    async def on_table_msg(self, db: DBI, *, msg_id, table_id):
        self.log.debug("on_table_msg: %s %s", msg_id, table_id)
        if not msg_id or not table_id:
            return
        msg = await db.get_table_msg(msg_id)
        if not msg:
            return
        msg = Message(msg.id, msg_type=msg.msg_type, table_id=msg.table_id, game_id=msg.game_id, cmd_id=msg.cmd_id, client_id=msg.client_id, **msg.props)
        if msg.client_id:
            # send directly to specific client
            client = self.clients.get(msg.client_id, None)
            subscribers = {msg.client_id: client} if client else None
        else:
            # send based on subscriptions
            subscribers = self.table_subscribers.get(msg.table_id, None)
        if not subscribers:
            return
        counter = 0
        for client in subscribers.values():
            if msg.msg_type == Message.Type.TABLE_INFO:
                if msg.table_redirect_id:
                    self.unsubscribe(client, msg.table_id)
                    self.subscribe(client, msg.table_redirect_id)
            cmsg = msg.hide_private_info(client.user_id)
            await client.handle_msg(cmsg)
            counter += 1
        self.log.info("on_table_msg: %s %s", counter, msg)
        
    def add_client(self, client: ClientBase):
        client.manager = self
        self.clients[client.client_id] = client

    def remove_client(self, client):
        for table_id in list(client.tables):
            self.unsubscribe(client, table_id)
        if client.client_id in self.clients:
            del self.clients[client.client_id]

    def subscribe(self, client, table_id):
        subscribers = self.table_subscribers.get(table_id, None)
        if subscribers is None:
            subscribers = {}
            self.table_subscribers[table_id] = subscribers
        subscribers[client.client_id] = client
        client.tables.add(table_id)

    def unsubscribe(self, client, table_id):
        if table_id not in client.tables:
            return
        client.tables.remove(table_id)
        subscribers = self.table_subscribers.get(table_id, None)
        if subscribers:
            subscribers.pop(client.client_id, None)
        # cleanup 
        if subscribers is not None and len(subscribers)==0:
            self.table_subscribers.pop(table_id, None)

    RESERVED_CMD_FIELDS = ['id','cmd_id','client_id']

    async def send_cmd(self, client, cmd: dict):
        if isinstance(cmd, Command):
            cmd.update(client_id = client.client_id)
        elif isinstance(cmd, dict):
            kwargs = {k:v for k,v in cmd if k not in self.RESERVED_CMD_FIELDS}
            cmd = Command(client_id = client.client_id, **kwargs)
        self.log.info("send_cmd: %s", str(cmd))
        async with DBI() as db:
            await db.create_table_cmd(client_id=client.client_id, table_id=cmd.table_id, cmd_type=cmd.cmd_type, props=cmd.props)
        
