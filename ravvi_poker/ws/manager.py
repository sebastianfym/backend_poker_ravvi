import logging
import json
import asyncio
from fastapi import WebSocket, WebSocketDisconnect, WebSocketException, status

from ..engine.events import Command, Message
from ..db.adbi import DBI
from ..db.listener import DBI_Listener
from ..api.utils import jwt_get
from .client import WS_Client


class WS_Manager(DBI_Listener):

    logger = logging.getLogger(__name__)

    def __init__(self):
        super().__init__()
        self.clients = {}
        self.table_subscribers = {}
        self.last_event_id = None
        self.channels = {
            "table_msg": self.on_table_msg
        }

    async def on_table_msg(self, db: DBI, *, id, type, table_id, client_id):
        self.log.debug("on_table_msg: %s %s %s %s", id, type, table_id, client_id)
        if not id or not table_id:
            return
        if client_id:
            # send directly to specific client
            client = self.clients.get(client_id, None)
            if not client:
                return
            subscribers = {client_id: client}
        else:
            # send based on subscriptions
            subscribers = self.table_subscribers.get(msg.table_id, {})

        if not subscribers:
            return
        msg = await db.get_table_msg(id)
        msg = Message(**msg)
        counter = 0
        for client in subscribers.values():
            if msg.msg_type == Message.Type.TABLE_INFO:
                self.unsubscribe(client, msg.table_id)
                self.subscribe(client, msg.table_redirect_id)
            await client.put_event(msg)
            counter += 1
        self.log.info("on_table_msg %s: %s", counter, msg)
        
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
        if subscribers and client.client_id in subscribers:
            del subscribers[client.client_id]
        # cleanup 
        if subscribers is not None and len(subscribers)==0:
            del self.table_subscribers[table_id]

    async def handle_cmd(self, client, cmd):
        self.log.info("handle_command: %s", str(cmd))
        table_id = cmd.pop('table_id', None)
        type = cmd.pop('type', None)
        async with DBI() as db:
            await db.create_table_cmd(client_id=client.client_id, table_id=table_id, cmd_type=type, user_id=client.user_id, **cmd)

    async def handle_connection(self, ws: WebSocket, access_token: str):
        # get session uuid from access_token
        session_uuid = jwt_get(access_token, "session_uuid")
        if not session_uuid:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
        # get session info
        async with DBI() as db:
            async with db.txn():
                session = await db.get_session_info(uuid=session_uuid)
                if not session:
                    raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
                row = await db.create_user_client(session_id=session.session_id)
        await ws.accept()
        client = WS_Client(self, ws, user_id=session.user_id, client_id=row.id)
        self.clients[client.client_id] = client
        try:
            await client.run()
        except Exception as ex:
            self.log.exception("ws: %s", ex)
        finally:
            for table_id in list(client.tables):
                self.unsubscribe(client, table_id)
            if client.client_id in self.clients:
                del self.clients[client.client_id]

        try:
            async with DBI() as db:
                async with db.txn():
                    await db.close_user_client(row.id)
        except:
            pass

