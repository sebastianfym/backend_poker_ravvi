import logging

from asyncio import Queue
from .event import Event

class Client:

    logger = logging.getLogger(__name__)

    def __init__(self, manager, user_id) -> None:
        self.manager = manager
        self.user_id = user_id
        self.queue = Queue()

    async def send(self, event):
        await self.queue.put(event)

    async def process_queue(self):
        while True:
            event : Event = await self.queue.get()
            event = self.process_event(event)
            try:
                await self.handle_event(event)
            except Exception as ex:
                self.logger.exception(" %s: %s", self.user_id, ex)
            self.queue.task_done()

    def process_event(self, event: Event):
        if event.type == Event.PLAYER_CARDS:
            if event.user_id != self.user_id and not event.cards_open:
                event = event.clone()
                cards = [0 for _ in event.cards]
                event.update(cards=cards, cards_open=None)
        elif event.type == Event.GAME_PLAYER_MOVE:
            if event.user_id != self.user_id:
                event = event.clone()
                event.update(options=[])
        return event
    
    async def handle_event(self, event: Event):
        pass


