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
    def __init__(self, websocket: WebSocket) -> None:
        self.ws = websocket

    async def handle_game_event(self, event):
        await self.ws.send_json(event)

    async def proccess_incoming_commands(self):
        while True:
            command = await self.ws.receive_json()
            

    async def run(self):


@router.websocket("/ws_test")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        session = WS_Session(websocket)
        manager.sessions.append(session)
        await session.run()
    except WebSocketDisconnect:
        manager.sessions.remove(session)
