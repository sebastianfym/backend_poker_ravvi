from asyncio import Queue
from .event import Event

class Client:

    def __init__(self, manager, user_id) -> None:
        self.manager = manager
        self.user_id = user_id
        self.queue = Queue()

    async def send(self, event):
        await self.queue.put(event)

    async def process_game_events(self):
        while True:
            event : Event = await self.queue.get()
            if event.type == Event.PLAYER_CARDS:
                if event.user_id != self.user_id and not event.cards_open:
                    cards = [0 for _ in event.cards]
                    event = Event(**event)
                    event.update(cards=cards, cards_open=None)
            elif event.type == Event.GAME_PLAYER_MOVE:
                if event.user_id != self.user_id:
                    event = Event(**event)
                    event.update(options=None)
            await self.handle_game_event(event)
            self.queue.task_done()

    async def handle_game_event(self, event):
        pass
    

