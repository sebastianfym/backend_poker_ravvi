import asyncio
from ravvi_poker_backend.db import DBI
from ravvi_poker_backend.events import Events

class GameReplay:

    def __init__(self, game_id) -> None:
        self.task = None
        self._stop_flag = None
        self.sessions = []

        self.game_id = game_id
        self.table_id = None
        self.events = None

    async def start(self):
        self._stop_flag = False
        self.task = asyncio.create_task(self.run())

    async def stop(self):
        self._stop_flag = True
        await self.task

    async def run(self):
        print(f"GameReplay({self.game_id}) started")
        self.load_data()
        await self.replay()
        print(f"GameReplay({self.game_id}) stopped")

    def load_data(self):
        with DBI() as db:
            with db.cursor() as cursor:
                cursor.execute("SELECT * FROM poker_game WHERE id=%s", (self.game_id,))
                row = cursor.fetchone()
                self.table_id = row.table_id
            with db.cursor() as cursor:
                cursor.execute("SELECT * FROM poker_events WHERE game_id=%s", (self.game_id,))
                self.events = cursor.fetchall()

    async def replay(self):
        seats = None
        game_active = False
        while not self._stop_flag:
            for event in self.events:
                #print(seats)
                if event.event_type==Events.TABLE_INFO:
                    seats = event.event_props.get('seats')
                elif event.event_type==Events.PLAYER_ENTER:
                    seat_id = event.event_props.get('seat_id')
                    seats[seat_id] = event.user_id
                elif event.event_type==Events.PLAYER_SEAT:
                    try:
                        seat_id = seats.index(event.user_id)
                        seats[seat_id] = None
                    except ValueError:
                        pass
                    seat_id = event.event_props.get('seat_id')
                    seats[seat_id] = event.user_id
                    

                # game status
                if event.event_type==Events.GAME_BEGIN:
                    game_active = True
                elif event.event_type==Events.GAME_END:
                    game_active = False

                # make payload
                payload = dict(
                    type=event.event_type, 
                    table_id=self.table_id
                )
                if game_active:
                    payload.update(game_id=self.game_id)
                if event.user_id:
                    payload.update(user_id=event.user_id)
                payload.update(event.event_props)

                await self.on_event(payload)

                # sleep
                if event.event_type in (Events.PLAYER_CARDS, Events.PLAYER_BID):
                    continue
                sleep_seconds = 2 
                if event.event_type==Events.GAME_PLAYER_MOVE:
                    sleep_seconds = 5 
                elif event.event_type==Events.GAME_END:
                    sleep_seconds = 5
                await asyncio.sleep(sleep_seconds)

    async def on_event(self, event):
        name = Events.name(event['type'])
        print(name, event)
        for s in self.sessions:
            await s.ws.send_json(event)


async def main():
    game = GameReplay(1)
    await game.start()
    await asyncio.sleep(5*60)
    await game.stop()

if __name__=="__main__":
    asyncio.run(main())
