import asyncio
from datetime import datetime
from .event import Event, TABLE_CLOSED
from .table_base import Table

class Table_SNG(Table):

    def __init__(self, id, *, table_type, blind_level_time, **kwargs):
        assert table_type == "SNG"
        super().__init__(id, table_type=table_type, **kwargs)
        self.started = None
        self.levels = LEVEL_SCHEDULE_STANDARD
        self.level_time = blind_level_time

    @property
    def take_seat_enabled(self):
        return self.started is None

    def on_user_seat_taken(self, user, user_seat_idx):
        user.balance = 10000

    async def run_table(self):
        # wait for players
        while not all(self.seats):
            await asyncio.sleep(1)

        self.started = datetime.utcnow().replace(microsecond=0)
        blind_small, blind_big, ante = self.levels[0] 

        users = self.get_players(2)
        while users:
            await asyncio.sleep(self.NEW_GAME_DELAY)
            await self.run_game(users, blind_value=blind_small)
            await asyncio.sleep(1)
            await self.remove_users(lambda u: u.balance<=0)
            await asyncio.sleep(1)

            now = datetime.utcnow().replace(microsecond=0)
            current_level = int((now - self.started).total_seconds()/60/self.level_time)
            current_level = min(current_level, len(self.levels)-1)
            blind_small, blind_big, ante = self.levels[0]


        await self.broadcast(TABLE_CLOSED())


LEVEL_SCHEDULE_STANDARD = [
(10, 20, 0),
(15,30,	0),
(20,40,	0),
(30,60,	5),
(40,80,	8),
(50,100,	10),
(75/150,	15),
(100,200,	20),
(125/250,	25),
(150,300,	30),
(200,400,	40),
(250,500,	50),
(300,600,	60),
(400,800,	80),
(500,1000,	100),
(600,1200,	120),
(700,1400,	140),
(800,1600,	160),
(1000,2000,	200),
(1200,2400,	250),
(1500,3000,	300),
(1800,3600,	350),
(2000,4000,	400),
(2500,5000,	500),
(3000,6000,	600),
(3500,7000,	700),
(4000,8000,	800),
(5000,10000,	1000),
(6000,12000,	1200),
(8000,16000,	1600),
(10000,20000,	2000),
(12000,24000,	2500),
(15000,30000,	3000),
(20000,40000,	4000),
(25000,50000,	5000),
(30000,60000,	6000),
(40000,80000,	8000),
(50000,100000,	10000),
(60000,120000,	10000),
(80000,160000,	15000),
(100000,200000,	20000),
(120000,240000,	25000),
(150000,300000,	30000),
(200000,400000,	40000),
(250000,500000,	50000),
(300000,600000,	60000),
(400000,800000,	80000),
(500000,1000000,	100000),
(600000,1200000,	120000),
(800000,1600000,	160000),
(1000000,2000000,	200000),
(1500000,3000000,	300000),
(2000000,4000000,	400000),
(2500000,5000000,	500000),
(3000000,6000000,	600000),
(4000000,8000000,	800000),
(5000000,10000000,	1000000),
(6000000,12000000,	1500000),
(8000000,16000000,	1500000),
(10000000,20000000,	2000000),
(15000000,30000000,	3000000),
(20000000,40000000,	4000000),
(25000000,50000000,	5000000),
(30000000,60000000,	6000000),
(40000000,80000000,	8000000),
(50000000,100000000,	10000000),
(60000000,120000000,	10000000),
(80000000,160000000,	15000000),
(100000000,200000000,	20000000),
(150000000,300000000,	30000000),
(200000000,400000000,	40000000),
(250000000,500000000,	50000000),
(300000000,600000000,	60000000),
(400000000,800000000,	80000000),
(500000000,1000000000,	100000000),
(600000000,1200000000,	100000000),
(800000000,1600000000,	150000000),
(1000000000,2000000000,	200000000),
(1500000000,3000000000,	300000000),
(2000000000,4000000000,	400000000)
]