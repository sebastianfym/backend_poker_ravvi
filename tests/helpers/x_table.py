import logging
import asyncio

from ravvi_poker.engine.user import User
from ravvi_poker.engine.events import Command, Message
from ravvi_poker.engine.table import Table
from ravvi_poker.engine.game import Game

from .x_utils import check_func_args
from .x_dbi import X_DBI


logger = logging.getLogger(__name__)

class X_Game(Game):
    DBI = X_DBI
    GAME_TYPE = 'X_GT'
    GAME_SUBTYPE = 'X_GST'

    @classmethod
    def check_methods_compatibility(cls):
        check_func_args(cls.run, Game.run)

    def __init__(self, table, users) -> None:
        super().__init__(table, users)
        self._stop = False

    async def run(self):
        async with self.table.lock:
            async with self.DBI() as db:
                await self.broadcast_GAME_BEGIN(db)

        while not self._stop:
            self.players_rotate()
            await asyncio.sleep(0.1)

        async with self.table.lock:
            p = self.current_player
            p.user.balance = max(0, p.user.balance-1)
            async with self.DBI() as db:
                await self.broadcast_GAME_END(db)


class X_Table(Table):
    DBI = X_DBI
    TABLE_TYPE = 'X'

    @classmethod
    def check_methods_compatibility(cls):
        #check_func_args(cls.user_enter_enabled, Table.user_enter_enabled)
        #check_func_args(cls.user_exit_enabled, Table.user_exit_enabled)
        check_func_args(cls.on_player_enter, Table.on_player_enter)
        check_func_args(cls.on_player_exit, Table.on_player_exit)
        check_func_args(cls.user_factory, Table.user_factory)
        check_func_args(cls.game_factory, Table.game_factory)

    def __init__(self, id, buyin_value):
        super().__init__(id, table_seats=9)
        self._user_enter_enabled = True
        self._user_exit_enabled = True
        self.buyin_value = buyin_value

    @property
    def user_enter_enabled(self):
        return self._user_enter_enabled

    @property
    def user_exit_enabled(self):
        return self._user_exit_enabled

    async def on_player_enter(self, db, user, seat_idx):
        logger.info("player enter %s -> %s", user.id, seat_idx)
        user.balance = self.buyin_value

    async def on_player_exit(self, db, user, seat_idx):
        logger.info("player exit %s <- %s", user.id, seat_idx)
        user.balance = 0

    async def user_factory(self, db, user_id):
        user = User(id=user_id, username='u'+str(user_id))
        #logger.info('user created: %s', user.__dict__)
        return user
    
    async def game_factory(self, users):
        return X_Game(self, users)

