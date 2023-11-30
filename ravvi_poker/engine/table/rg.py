from .base import Table, DBI

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

    async def on_player_enter(self, db: DBI, user, seat_idx):
        # lobby: get user_profile balance
        account = await db.get_user(user.id)
        if not account:
            return False
        buyin = self.buyin_min
        new_balance = account.balance-buyin
        self.log.info("user %s buyin %s -> balance %s", user.id, buyin, new_balance)
        if new_balance<0:
            return False
        await db.update_user(user.id, balance=new_balance)
        user.balance = buyin
        return True

    async def on_player_exit(self, db, user, seat_idx):
        account = await db.get_user(user.id)
        new_balance = account.balance+user.balance
        self.log.info("user %s exit %s -> balance %s", user.id, user.balance, new_balance)
        await db.update_user(user.id, balance=new_balance)
        user.balance = None
