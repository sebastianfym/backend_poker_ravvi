from decimal import Decimal, ROUND_HALF_DOWN

from psycopg.rows import Row

from .base import Table, DBI
from ..events import Message
from ..user import User
from .rg import Table_RG

class Table_RG_Lobby(Table_RG):
    TABLE_TYPE = "RG"

    async def on_player_enter(self, db: DBI, cmd_id, client_id, user: User, seat_idx):
        # lobby: get user_profile balance
        account = await db.get_account_for_update(user.account_id)
        if not account:
            return False
        table_session = await db.register_table_session(table_id=self.table_id, account_id=account.id)
        user.table_session_id = table_session.id
        await self.handle_auto_buyin(db, user, account)
        self.log.info("on_player_enter(%s): done", user.id)
        return True

    async def on_player_exit(self, db: DBI, user, seat_idx):
        account = await db.get_account_for_update(user.account_id)
        if user.balance is not None:
            new_account_balance = account.balance + user.balance
            self.log.info("user %s exit %s -> balance %s", user.id, user.balance, new_account_balance)
            await db.create_account_txn(user.account_id, "REWARD", user.balance, sender_id=self.table_id,
                                        table_id=self.table_id)
            user.balance = None
        if user.table_session_id:
            await db.close_table_session(user.table_session_id)
            user.table_session_id = None
        self.log.info("on_player_exit(%s): done", user.id)


    async def handle_auto_buyin(self, db, user, account):
        buyin = self.buyin_min
        new_account_balance = account.balance - buyin
        self.log.info("user %s buyin %s -> balance %s", user.id, buyin, new_account_balance)
        # if new_balance < 0:
        #    return False
        await db.create_account_txn(user.account_id, "BUYIN", -buyin, sender_id=None, table_id=self.table_id)
        user.balance = buyin

    async def on_table_continue(self):
        # пополним балансы пользователей, которые все проиграли
        async with self.DBI() as db:
            users_on_table = [u for u in self.seats if u and u.balance==0]
            for user in users_on_table:
                account = await db.get_account_for_update(user.account_id)
                if not account:
                    return False
                await self.handle_auto_buyin(db, user, account)
                await self.broadcast_PLAYER_BALANCE(db, user_id=user.id, balance=user.balance)
        
        await super().on_table_continue()
