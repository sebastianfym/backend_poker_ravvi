import logging

from asyncio import Queue
from ..logging import ObjectLogger
from .event import Event



class Client(ObjectLogger):

    def __init__(self, manager, user_id, *, logger_name=None) -> None:
        logger_name = logger_name or (__name__+f".{id(self)}")
        super().__init__(logger_name)
        self.client_id = id(self)
        self.manager = manager
        self.user_id = user_id
        self.tables = set()
        self.queue = Queue()

    async def dispatch_command(self, command):
        try:
            self.log_debug("dispatch_command %s", command)
            await self.manager.dispatch_command(self, command)
        except Exception as ex:
            self.log_exception("dispatch_command: %s", ex)
            raise

    async def send_event(self, event):
        await self.queue.put(event)

    async def process_queue(self):
        while True:
            event : Event = await self.queue.get()
            event = self.process_event(event)
            try:
                self.log_debug("handle_event: %s", event)
                await self.handle_event(event)
            except Exception as ex:
                self.log_exception("handle_event: %s", ex)
            finally:
                self.queue.task_done()

    def process_event(self, event: Event):
        event = event.clone()
        if event.type == Event.PLAYER_CARDS:
            if event.user_id != self.user_id and not event.cards_open:
                cards = [0 for _ in event.cards]
                event.update(cards=cards)
            del event['cards_open']
        elif event.type == Event.GAME_PLAYER_MOVE:
            if event.user_id != self.user_id:
                del event['options']
        return event
    
    async def handle_event(self, event: Event):
        pass


