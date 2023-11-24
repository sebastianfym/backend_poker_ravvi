from .base import Table

class Table_REGULAR(Table):

    TABLE_TYPE = "REGULAR"

    def __init__(self, id, *, buyin_min=1000, buyin_max=None, **kwargs):
        base, kwargs = super().split_kwargs(**kwargs)
        super().__init__(id, **base)
        self.buyin_min = buyin_min
        self.buyin_max = buyin_max

    @property
    def user_enter_enabled(self):
        return True

    @property
    def user_exit_enabled(self):
        return True
    
    def on_user_seat_taken(self, user, user_seat_idx):
        user.balance = self.buyin_min

#    async def run_table(self):
#        while True:
#            await self.sleep(self.NEW_GAME_DELAY)
#            # try to start new game
#            users = self.get_players(2)
#            if users:
#                await self.run_game(users)
#            await self.remove_users()
