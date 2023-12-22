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
        self.listener = DBI_Listener(log=self.log)
        self.listener.channels = {
            "table_msg": self.on_table_msg,
            "user_client_closed": self.on_user_client_closed,
        }

    async def start(self):
        await self.listener.start()

    async def stop(self):
        self.log.info("shutdown clients ...")
        # сигнализируем остановку для всех клиентов
        for x in list(self.clients.values()):
            await x.shutdown()
        # ждем завершения работы всех клиентов
        await self._wait_client_closed()
        self.log.info("shutdown clients done")
        # выключаем прием оповещений
        await self.listener.stop()

    async def _wait_client_closed(self):
        while self.clients:
            await asyncio.sleep(0.1)

    async def on_table_msg(self, *, msg_id, table_id):
        if not msg_id or not table_id:
            return
        async with DBI() as dbi:
            msg = await dbi.get_table_msg(msg_id)
        if not msg:
            return
        msg = Message(msg.id, msg_type=msg.msg_type, table_id=msg.table_id, game_id=msg.game_id, cmd_id=msg.cmd_id, client_id=msg.client_id, **msg.props)
        #self.log.debug("on_table_msg: %s %s %s", msg_id, msg.msg_type, msg.props)
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

    async def on_user_client_closed(self, *, client_id):
        self.log.info("on_user_client_closed %s", client_id)
        client = self.clients.pop(client_id, None)
        if not client:
            return
        # удаление клиента из подписок на столы
        for table_id in list(client.tables):
            self.unsubscribe(client, table_id)
        # ожидание завершения внтуреннего цикла
        await client.wait_done()
        
    async def start_client(self, client: ClientBase):
        client.manager = self
        self.clients[client.client_id] = client
        await client.start()
        self.log.debug('client %s started', client.client_id)

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
