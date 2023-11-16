import logging
import asyncio
from contextlib import suppress
from fastapi import WebSocket, WebSocketDisconnect, WebSocketException, status
from starlette.websockets import WebSocketState

from ..logging import ObjectLogger
from ..game.event import Event
from ..db.adbi import DBI
from ..api.utils import jwt_get

logger = logging.getLogger(__name__)

class WS_Client(ObjectLogger):
    def __init__(self, manager, ws, user_id, client_id, *, logger_name=None) -> None:
        logger_name = logger_name or (__name__ + f".{client_id}")
        super().__init__(logger_name)
        self.manager = manager
        self.ws = ws
        self.user_id = user_id
        self.client_id = client_id
        self.tables = set()
        self.queue = asyncio.Queue()

    @property
    def is_connected(self):
        return self.ws.client_state == WebSocketState.CONNECTED

    async def put_event(self, event):
        await self.queue.put(event)

    async def run_queue(self):
        while self.is_connected:
            event: Event = await self.queue.get()
            try:
                self.log_debug("process_event: %s", event)
                event = self.handle_event(event)
                await self.send_event(event)
            except asyncio.CancelledError:
                break
            except Exception as ex:
                self.log_exception("process_event: %s: %s", event, ex)
            finally:
                self.queue.task_done()

    def handle_event(self, event: Event):
        event = event.clone()
        if event.type == Event.PLAYER_CARDS:
            if event.user_id != self.user_id and not event.cards_open:
                cards = [0 for _ in event.cards]
                event.update(cards=cards)
                event.pop("hand_type", None)
                event.pop("hand_cards", None)
            del event["cards_open"]
        elif event.type == Event.GAME_PLAYER_MOVE:
            if event.user_id != self.user_id:
                del event["options"]
        return event

    async def send_event(self, event: Event):
        if self.is_connected:
            await self.ws.send_json(event)

    async def recv_commands(self):
        try:
            while self.is_connected:
                command = await self.ws.receive_json()
                await self.manager.handle_command(self, command)
        except asyncio.CancelledError:
            self.log_debug("CancelledError")
        except WebSocketDisconnect:
            self.log_debug("WebSocketDisconnect")
        except Exception as ex:
            self.log_exception(" %s: %s", self.user_id, ex)

    async def run(self):
        self.log_info("begin")
        try:
            t1 = asyncio.create_task(self.recv_commands())
            t2 = asyncio.create_task(self.run_queue())
            await t1
            t2.cancel()
            with suppress(asyncio.exceptions.CancelledError):
                await t2
        finally:
            self.log_info("end")

