import decimal

from .base import Table, DBI


class Table_RG(Table):
    TABLE_TYPE = "RG"

    def parse_props(self, buyin_min=100, buyin_max=None, blind_small: float = 0.01,
                    blind_big: float | None = None, ante_up: bool | None = None,
                    action_time=30, **kwargs):
        from ..poker.ante import AnteUpController
        from ..poker.bomb_pot import BombPotController

        self.buyin_min = buyin_min
        self.buyin_max = buyin_max
        self.game_props.update(bet_timeout=action_time, blind_small=blind_small,
                               blind_big=blind_big if blind_big is not None else blind_small * 2)

        if ante_up:
            self.ante = AnteUpController(blind_small)
            if len(self.ante.ante_levels) != 0:
                self.game_props.update(ante=self.ante.current_ante_value)
        if bompot_settings := getattr(self, "game_modes_config").bombpot_settings:
            self.bombpot = BombPotController(bompot_settings)
            # TODO согласовать что отправлять

    @property
    def user_enter_enabled(self):
        return True

    @property
    def user_exit_enabled(self):
        return True

    async def on_player_enter(self, db: DBI, user, seat_idx):
        # lobby: get user_profile balance
        account = await db.get_account_for_update(user.account_id)
        if not account:
            return False
        table_session = await db.register_table_session(table_id=self.table_id, account_id=account.id)
        user.table_session_id = table_session.id
        buyin = self.buyin_min
        # TODO: точность и округление
        new_account_balance = float(account.balance) - buyin
        self.log.info("user %s buyin %s -> balance %s", user.id, buyin, new_account_balance)
        # if new_balance < 0:
        #    return False
        await db.create_account_txn(user.account_id, "BUYIN", -buyin, sender_id=self.table_id)
        user.balance = buyin
        self.log.info("on_player_enter(%s): done", user.id)
        return True

    async def on_player_exit(self, db: DBI, user, seat_idx):
        account = await db.get_account_for_update(user.account_id)
        if user.balance is not None:
            # TODO: точность и округление
            new_account_balance = float(account.balance) + user.balance
            self.log.info("user %s exit %s -> balance %s", user.id, user.balance, new_account_balance)
            await db.create_account_txn(user.account_id, "CASHOUT", user.balance, sender_id=self.table_id)
            user.balance = None
        if user.table_session_id:
            await db.close_table_session(user.table_session_id)
            user.table_session_id = None
        self.log.info("on_player_exit(%s): done", user.id)
