import logging
import asyncio
from contextlib import suppress, asynccontextmanager
from fastapi import APIRouter
from fastapi import WebSocket, WebSocketDisconnect, WebSocketException, status
from starlette.websockets import WebSocketState

from .utils import jwt_get
from ..game.manager import Manager
from ..game.client import Client
from ..engine.event import Event
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

    @property
    def is_connected(self):
        return self.ws.client_state == WebSocketState.CONNECTED

    async def handle_event(self, event: Event):
        if self.is_connected:
            await self.ws.send_json(event)

    async def process_commands(self):
        try:
            while self.is_connected:
                command = await self.ws.receive_json()
                command = Event(**command)
                await self.dispatch_command(command)
        except asyncio.CancelledError:
            self.log_debug("CancelledError")
        except WebSocketDisconnect:
            self.log_debug("WebSocketDisconnect")
        except Exception as ex:
            self.log_exception(" %s: %s", self.user_id, ex)

    async def run(self):
        self.log_info("begin")
        try:
            t1 = asyncio.create_task(self.process_commands())
            t2 = asyncio.create_task(self.process_queue())
            await t1
            t2.cancel()
            with suppress(asyncio.exceptions.CancelledError):
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
        logger.exception("ws: %s", ex)
 