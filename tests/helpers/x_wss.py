import logging
import asyncio
from fastapi import WebSocketDisconnect
from starlette.websockets import WebSocketState

logger = logging.getLogger(__name__)

class X_WSS_ClientManager:

    def __init__(self) -> None:
        self._commands = []
        self._messages = []

    async def handle_cmd(self, client, cmd):
        logger.info("%s/%s -> %s", client.user_id, client.client_id, cmd)
        self._commands.append(cmd)
        while True:
            if not self._messages:
                logger.info('no messages')
                break
            msg = self._messages.pop(0)
            if msg == None:
                logger.info('break')
                break
            logger.info('put_msg: %s', msg)
            await client.put_msg(msg)


class X_WebSocket:
    def __init__(self) -> None:
        self._commands = []
        self._messages = []

    @property
    def client_state(self):
        return WebSocketState.CONNECTED if self._commands else None
    
    async def accept(self):
        pass

    async def receive_json(self):
        while True:
            if not self._commands:
                raise WebSocketDisconnect()
            cmd = self._commands[0]
            if isinstance(cmd, (int, float)):
                logger.info('receive_json: sleep %s', cmd)
                await asyncio.sleep(cmd)
                self._commands.pop(0)
            else:
                self._commands.pop(0)
                return cmd

    async def send_json(self, msg):
        self._messages.append(msg)