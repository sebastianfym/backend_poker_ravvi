import logging
from starlette.websockets import WebSocket, WebSocketState
from fastapi import WebSocketDisconnect

from .base import ClientQueue, Message, ClientsManager

logger = logging.getLogger(__name__)


class ClientWS(ClientQueue):
    
    def __init__(self, manager: ClientsManager, client_id, user_id, ws: WebSocket) -> None:
        super().__init__(manager, client_id, user_id)
        self.log.logger = logger
        self.ws = ws
        self.log.debug('new ws client created')

    @property
    def is_connected(self):
        return self.ws.client_state == WebSocketState.CONNECTED

    async def on_msg(self, msg: Message):
        data = dict(msg)
        # remove system internal props
        for k in ('cmd_id','client_id'):
            data.pop(k,None)
        # move props to top level
        props = data.pop('props')
        data.update(props)
        self.log.debug("send_json: %s", data)
        await self.ws.send_json(data)

    async def on_shutdown(self):
        if self.is_connected:
            await self.ws.close()

    async def recv_commands(self):
        self.log.info('recv_commands: ...')
        try:
            while self.is_connected:
                cmd = await self.ws.receive_json()
                self.log.debug("cmd: %s", cmd)
                await self.send_cmd(cmd)
        except WebSocketDisconnect:
            self.log.info("disconnect")
        except Exception as ex:
            self.log.exception(" %s: %s", self.user_id, ex)
        finally:
            await super().on_shutdown()
