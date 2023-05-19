import asyncio
from fastapi import APIRouter, Depends, Query
from fastapi import WebSocket, WebSocketDisconnect, WebSocketException, status
from ..game.manager import Manager
from ..game.client import Client
from ..game.event import Event
from ..api.utils import jwt_get
from ..db.dbi import DBI

router = APIRouter(tags=["ws"])

manager = Manager()

@router.on_event('startup')
async def app_startup():
    await manager.start()

@router.on_event('shutdown')
async def app_shutdown():
    await manager.stop()

class WS_Client(Client):
    
    def __init__(self, websocket: WebSocket, user_id) -> None:
        super().__init__(manager, user_id)
        self.ws = websocket

    async def handle_event(self, event):
        event = Event(**event)
        if event.user_id != self.user_id:
            event.update(options=[])
        await self.ws.send_json(event)

    async def proccess_commands(self):
        while True:
            command = await self.ws.receive_json()
            command = Event(**command)
            await manager.dispatch_command(self, command)

    async def run(self):
        await manager._add_client(self)
        t1 = asyncio.create_task(self.proccess_commands())
        t2 = asyncio.create_task(self.process_queue())
        await t1
        await t2


@router.websocket("/ws_test")
async def websocket_endpoint(websocket: WebSocket, access_token: str = None):
    session_uuid = jwt_get(access_token, "session_uuid")
    if not session_uuid:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    with DBI() as dbi:
        session = dbi.get_session_info(uuid=session_uuid)
        if not session:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
        user = dbi.get_user(id=session.user_id)
        if not user:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    await websocket.accept()
    try:
        client = WS_Client(websocket, user_id=user.id)
        await client.run()
    except WebSocketDisconnect:
        pass
    finally:
        await manager.remove_client(client)
