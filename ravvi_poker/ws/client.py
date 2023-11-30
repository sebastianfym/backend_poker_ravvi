import asyncio
from contextlib import suppress
from fastapi import WebSocket, WebSocketDisconnect, WebSocketException, status
from starlette.websockets import WebSocketState

from ..logging import ObjectLoggerAdapter, getLogger
from ..engine.events import Message, Command

logger = getLogger(__name__)

class WS_Client:
    def __init__(self, manager, ws: WebSocket, user_id, client_id) -> None:
        self.manager = manager
        self.ws = ws
        self.user_id = user_id
        self.client_id = client_id
        self.log = ObjectLoggerAdapter(logger, lambda: self.client_id)
        self.tables = set()
        self.queue = asyncio.Queue()

    @property
    def is_connected(self):
        return self.ws.client_state == WebSocketState.CONNECTED

    async def put_msg(self, msg: Message):
        await self.queue.put(msg)

    async def run_msg_queue(self):
        self.log.debug("run_msg_queue: begin")
        while self.is_connected:
            msg: Message = await self.queue.get()
            try:
                await self.send_msg(msg)
            except asyncio.CancelledError:
                self.log.info("run_msg_queue: cancelled")
                break
            except Exception as e:
                self.log.exception("msg: %s: %s", msg, e)
                break
            finally:
                self.queue.task_done()
        self.log.debug("run_msg_queue: end")

    async def send_msg(self, msg: Message):
        if not self.is_connected:
            return
        msg = msg.hide_private_info(self.user_id)
        await self.ws.send_json(msg)
        self.log.info('send_msg: %s', msg)

    async def recv_commands(self):
        self.log.info('recv_commands: ...')
        try:
            while self.is_connected:
                cmd = await self.ws.receive_json()
                await self.handle_cmd(cmd)
        except asyncio.CancelledError:
            self.log.debug("cancel")
        except WebSocketDisconnect:
            self.log.debug("disconnect")
        except Exception as ex:
            self.log.exception(" %s: %s", self.user_id, ex)

    async def handle_cmd(self, cmd: dict):
        cmd.pop('id', None)
        cmd.pop('client_id', None)
        cmd = Command(client_id = self.client_id, **cmd)
        await self.manager.handle_cmd(self, cmd)

    async def run(self):
        self.log.info("begin")
        try:
            msg_task = asyncio.create_task(self.run_msg_queue())
            await self.recv_commands()
            msg_task.cancel()
            with suppress(asyncio.exceptions.CancelledError):
                await msg_task
        finally:
            self.log.info("end")