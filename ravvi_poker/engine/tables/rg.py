import decimal

from .base import Table, DBI


class Table_RG(Table):
    TABLE_TYPE = "RG"

    def parse_props(self, buyin_min=100, buyin_max=None, bet_timeout=15, blind_small: float = 0.01,
                    blind_big: float | None = None, ante_up: bool | None = None, **kwargs):
        self.buyin_min = buyin_min
        self.buyin_max = buyin_max
        self.game_props.update(bet_timeout=bet_timeout, blind_small=blind_small,
                               blind_big=blind_big if blind_big is not None else blind_small * 2,
                               ante_up=ante_up)
        self.game_props.update(ante_levels=self.calc_rg_ante_levels())

    def calc_rg_ante_levels(self) -> list:
        if self.game_props["ante_up"]:
            if self.game_props["blind_small"] == 0.02:
                return [0.01, 0.02]
            elif self.game_props["blind_small"] in [0.03, 0.04]:
                return [0.01, 0.02, 0.03]
            else:
                return [round(self.game_props["blind_small"] * 2 * multiplier, 2) for multiplier in [0.2, 0.3, 0.4, 0.5]]
        else:
            return []

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
        await db.create_account_txn(user.account_id, "BUYIN", -buyin)
        user.balance = buyin
        self.log.info("on_player_enter(%s): done", user.id)
        return True

    async def on_player_exit(self, db: DBI, user, seat_idx):
        account = await db.get_account_for_update(user.account_id)
        if user.balance is not None:
            # TODO: точность и округление
            new_account_balance = float(account.balance) + user.balance
            self.log.info("user %s exit %s -> balance %s", user.id, user.balance, new_account_balance)
            await db.create_account_txn(user.account_id, "CASHOUT", user.balance)
            user.balance = None
        if user.table_session_id:
            await db.close_table_session(user.table_session_id)
            user.table_session_id = None
        self.log.info("on_player_exit(%s): done", user.id)
