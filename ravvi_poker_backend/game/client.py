from asyncio import Queue

class Client:

    def __init__(self, user_id) -> None:
        self.user_id = user_id
        self.queue = Queue()

    async def send(self, event):
        await self.queue.put(event)

    async def process_game_events(self):
        while True:
            event = await self.queue.get()
            await self.handle_game_event(event)

    async def handle_game_event(self, event):
        pass
    
    async def dispatch_command(self, event):
        pass

