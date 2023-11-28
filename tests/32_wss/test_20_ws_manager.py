import logging
import pytest

from ravvi_poker.db.dbi import DBI
from ravvi_poker.engine.events import Command, Message
from ravvi_poker.engine.jwt import jwt_encode
from ravvi_poker.ws.manager import WS_Manager
from ravvi_poker.ws.client import WS_Client

from helpers.x_wss import X_WebSocket
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_ws_manager(table, access):
    session_info, access_token = access
    x_ws = X_WebSocket()

    manager = WS_Manager()
    assert not manager.clients
    assert not manager.table_subscribers
    
    client = await manager.handle_connect(x_ws, access_token=access_token)
    assert client.user_id == session_info.user_id
    assert not client.tables
    assert manager.clients
    assert not manager.table_subscribers

    await client.handle_cmd(dict(table_id=table.id, cmd_type=Command.Type.JOIN, take_seat=True))
    async with DBI() as db:
        msg = await db.create_table_msg(table_id=table.id, game_id=None, msg_type=Message.Type.TABLE_INFO, props=dict(table_redirect_id=table.id), client_id=client.client_id)
        await manager.on_table_msg(db, msg_id=msg.id, table_id=table.id)
    assert manager.clients
    assert manager.table_subscribers
    subscribers = manager.table_subscribers.get(table.id)
    assert subscribers
    assert client.client_id in subscribers
    assert table.id in client.tables


    await manager.handle_disconnect(client)
    assert not manager.clients
    assert not manager.table_subscribers
    assert not client.tables
