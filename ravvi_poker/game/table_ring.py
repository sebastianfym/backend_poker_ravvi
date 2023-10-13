import asyncio

from .table_base import Table

class Table_RING(Table):

    def __init__(self, id, *, table_type, **kwargs):
        assert table_type == "RING_GAME"
        super().__init__(id, table_type=table_type, **kwargs)

    def on_user_seat_taken(self, user, user_seat_idx):
        user.balance = 1000

    async def run_table(self):
        while True:
            await asyncio.sleep(self.NEW_GAME_DELAY)

            # set user balances
            for u in self.seats:
                if not u:
                    continue
                if u.balance<=0:
                    u.balance = 1000

            # try to start new game
            users = self.get_players(2)
            if users:
                await self.run_game(users)
            await asyncio.sleep(1)
            await self.remove_users(lambda u: not u.connected)
            await asyncio.sleep(1)
