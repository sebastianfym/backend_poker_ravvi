import asyncio
from fastapi import APIRouter, Depends
from fastapi import WebSocket, WebSocketDisconnect
from ..drafts.game_replay import GameReplay

router = APIRouter(tags=["ws"])

manager = GameReplay(1)

@router.on_event('startup')
async def app_startup():
    await manager.start()

@router.on_event('shutdown')
async def app_shutdown():
    await manager.stop()

class WS_Session:
    def __init__(self, websocket) -> None:
        self.ws = websocket
    
    async def run(self):
        while True:
            data = await self.ws.receive_json()


@router.websocket("/ws_test")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        session = WS_Session(websocket)
        manager.sessions.append(session)
        await session.run()
    except WebSocketDisconnect:
        manager.sessions.remove(session)
