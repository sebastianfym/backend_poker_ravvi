from starlette.websockets import WebSocket, WebSocketState
from fastapi import WebSocketDisconnect

from .base import ClientQueue, Message

class ClientWS(ClientQueue):
    
    def __init__(self, ws: WebSocket, client_id, user_id) -> None:
        super().__init__(client_id, user_id)
        self.ws = ws

    @property
    def is_connected(self):
        return self.ws.client_state == WebSocketState.CONNECTED

    async def on_msg(self, msg: Message):
        self.log.info("on_msg: %s", msg)
        await self.ws.send_json(msg)

    async def on_shutdown(self):
        if self.is_connected:
            self.ws.close()

    async def recv_commands(self):
        self.log.info('recv_commands: ...')
        try:
            while self.is_connected:
                cmd = await self.ws.receive_json()
                self.log.info("cmd: %s", cmd)
                await self.send_cmd(cmd)
        except WebSocketDisconnect:
            self.log.info("disconnect")
        except Exception as ex:
            self.log.exception(" %s: %s", self.user_id, ex)
        finally:
            if self.is_connected:
                await self.ws.close()
            await super().on_shutdown()
