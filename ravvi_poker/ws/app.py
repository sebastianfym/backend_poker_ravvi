import logging
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi import WebSocket, WebSocketDisconnect, WebSocketException, status
from fastapi.middleware.cors import CORSMiddleware
from ..db.adbi import DBI
from .manager import WS_Manager

logger = logging.getLogger(__name__)

manager = WS_Manager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # statup begin
    await DBI.pool_open()
    await manager.start()
    # statup end
    yield
    # shutdown begin
    await manager.stop()
    await DBI.pool_close()
    # shutdown end


app = FastAPI(lifespan=lifespan)

@app.websocket("/v1/ws")
async def v1_ws_endpoint(ws: WebSocket, access_token: str = None):
    await manager.handle_connection(ws, access_token)
