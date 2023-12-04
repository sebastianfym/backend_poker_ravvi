import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter, WebSocket, WebSocketDisconnect, WebSocketException, status
from fastapi.middleware.cors import CORSMiddleware
from ..db import DBI
from ..engine.jwt import jwt_get
from ..engine.clients import ClientsManager
from ..engine.clients.ws import ClientWS
from .utils import SessionUUID, get_session_and_user

logger = logging.getLogger(__name__)

manager = ClientsManager()

router = APIRouter(tags=["ws"])

@router.websocket("/ws")
async def v1_ws_endpoint(ws: WebSocket, access_token: str = None):
    # get session uuid from access_token
    session_uuid = jwt_get(access_token, "session_uuid")
    if not session_uuid:
        raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
    # get session info
    async with DBI() as db:
        session = await db.get_session_info(uuid=session_uuid)
        if not session:
            raise WebSocketException(code=status.WS_1008_POLICY_VIOLATION)
        row = await db.create_client(session_id=session.session_id)
    await ws.accept()
    # create client object
    client = ClientWS(ws, user_id=session.user_id, client_id=row.id)
    # start client with manager
    await manager.start_client(client)
    # process incoming commands
    await client.recv_commands()
