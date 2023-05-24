import logging
import asyncio
from fastapi import APIRouter
from fastapi import WebSocket, WebSocketDisconnect, WebSocketException, status

from .utils import jwt_get
from ..game.manager import Manager
from ..game.client import Client
from ..game.event import Event
from ..db.dbi import DBI

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ws"])

manager = Manager()

@router.on_event('startup')
async def app_startup():
    await manager.start()

@router.on_event('shutdown')
async def app_shutdown():
    await manager.stop()

class WS_Client(Client):
    
    def __init__(self, websocket: WebSocket, user_id: int) -> None:
        super().__init__(manager, user_id)
        self.ws = websocket

    async def handle_event(self, event: Event):
        await self.ws.send_json(event)

    async def process_commands(self):
        try:
            while True:
                command = await self.ws.receive_json()
                command = Event(**command)
                await self.dispatch_command(command)
        except Exception as ex:
            self.exception(" %s: %s", self.user_id, ex)

    async def run(self):
        self.log_info("begin")
        try:
            t1 = asyncio.create_task(self.process_commands())
            t2 = asyncio.create_task(self.process_queue())
            await t1
            await t2
        finally:
            await self.manager.remove_client(self)
            self.log_info("end")


@router.websocket("/ws")
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
    except Exception as ex:
        logger.error("ws: %s", ex)
