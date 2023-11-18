import logging
import json
import asyncio
from fastapi import WebSocket, WebSocketDisconnect, WebSocketException, status

from ..engine.event import Event
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
        self.channels = dict(
            poker_event_msg = self.on_poker_event_msg
        )

    async def on_poker_event_msg(self, db: DBI, *, id, type, table_id, client_id):
        if not id or table_id:
            return
        counter = 0
        if client_id:
            # send directly to specific client
            client = self.clients.get(client_id, None)
            if not client:
                return
            event_row = db.get_event(id)
            event = Event.from_row(event_row)
            client.put_event(event)
            counter += 1
            if event.type == Event.TABLE_INFO:
                self.unsubscribe(client, event.table_id)
                self.subscribe(client, event.table_redirect_id)
        else:
            # send based on subscriptions
            subscribers = self.table_subscribers.get(event.table_id, {})
            if subscribers:
                event_row = db.get_event(id)
                event = Event.from_row(event_row)
            for client in subscribers.values():
                client.put_event(event)
                counter += 1
        if counter:
            self.log_info("on_poker_event_cmd %s: %s", counter, event)
        
    def subscribe(self, client, table_id):
        subscribers = self.table_subscribers.get(table_id, None)
        if subscribers is None:
            subscribers = {}
            self.table_subscribers[table_id] = subscribers
        subscribers[client.client_id] = client
        client.tables.add(table_id)

    def unsubscribe(self, client, table_id):
        subscribers = self.table_subscribers.get(table_id, None)
        if subscribers and client.cliend_id in subscribers:
            del subscribers[client.cliend_id]
        client.tables.remove(table_id)
        # cleanup 
        if subscribers is not None and len(subscribers)==0:
            del self.table_subscribers[table_id]

    async def handle_command(self, client, cmd):
        self.log_info("handle_command: %s", str(cmd))
        table_id = cmd.pop('table_id', None)
        type = cmd.pop('type', None)
        async with DBI() as db:
            async with db.txn():
                await db.save_event(table_id=table_id, type=type, client_id=client.client_id, user_id=client.user_id, **cmd)

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
        self.clients[client.client_id] = client.client_id
        try:
            await client.run()
        except Exception as ex:
            self.log_exception("ws: %s", ex)
        finally:
            for table_id in client.tables:
                self.unsubscribe(client, table_id)
            if client.client_id in self.clients:
                del self.clients[client.client_id]

        try:
            async with DBI() as db:
                async with db.txn():
                    await db.close_user_client(row.id)
        except:
            pass
