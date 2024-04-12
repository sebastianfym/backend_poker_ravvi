from decimal import Decimal, ROUND_HALF_DOWN

from psycopg.rows import Row

from .base import Table, DBI
from ..events import Message
from ..user import User
from .rg import Table_RG

class Table_RG_Lobby(Table_RG):
    TABLE_TYPE = "RG"

    async def on_player_enter(self, db: DBI, cmd_id, client_id, user: User, seat_idx):
        table_session = await db.register_table_session(table_id=self.table_id, account_id=user.account_id)
        user.table_session_id = table_session.id
        await self.handle_auto_buyin(db, user)
        self.log.info("on_player_enter(%s): done", user.id)
        return True

    async def on_player_exit(self, db: DBI, user, seat_idx):
        if user.balance is not None:
            # TODO: error handling
            await db.create_txn_REWARD(member_id=user.account_id, table_session_id=user.table_session_id, txn_value=user.balance)
            user.balance = None
        if user.table_session_id:
            await db.close_table_session(user.table_session_id)
            user.table_session_id = None
        self.log.info("on_player_exit(%s): done", user.id)

    async def handle_auto_buyin(self, db: DBI, user):
        buyin = self.buyin_min
        # TODO: error handling
        await db.create_txn_BUYIN(member_id=user.account_id, table_session_id=user.table_session_id, txn_value=buyin)
        user.balance = buyin

    async def on_table_continue(self):
        # пополним балансы пользователей, которые все проиграли
        async with self.DBI() as db:
            users_on_table = [u for u in self.seats if u and u.balance==0]
            for user in users_on_table:
                await self.handle_auto_buyin(db, user)
                await self.broadcast_PLAYER_BALANCE(db, user_id=user.id, balance=user.balance)
        
        await super().on_table_continue()
