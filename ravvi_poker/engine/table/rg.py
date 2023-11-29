from .base import Table

class Table_RG(Table):
    TABLE_TYPE = "RG"

    def parse_props(self, buyin_min=100, buyin_max=None, bet_timeout=15, **kwargs):
        self.buyin_min = buyin_min
        self.buyin_max = buyin_max
        self.game_props.update(
            bet_timeout = bet_timeout
        )

    @property
    def user_enter_enabled(self):
        return True

    @property
    def user_exit_enabled(self):
        return True

    async def on_player_enter(self, db, user, seat_idx):
        user.balance = self.buyin_min

#    async def run_table(self):
#        while True:
#            await self.sleep(self.NEW_GAME_DELAY)
#            # try to start new game
#            users = self.get_players(2)
#            if users:
#                await self.run_game(users)
#            await self.remove_users()
