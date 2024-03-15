import asyncio
import logging

from ravvi_poker.engine.game import Game
from ravvi_poker.engine.tables import Table
from ravvi_poker.engine.user import User
from .x_dbi import X_DBI
from .x_utils import check_func_args

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
        check_func_args(cls.on_player_enter, Table.on_player_enter)
        check_func_args(cls.on_player_exit, Table.on_player_exit)
        check_func_args(cls.user_factory, Table.user_factory)
        check_func_args(cls.game_factory, Table.game_factory)

    def __init__(self, id, table_name, buyin_value, game_props=None, props=None):
        # если не были переданы свойства - замокаем необходимые
        if props is None:
            props = self.mock_necessary_table_props()

        super().__init__(id, table_name, table_seats=9, club_id=0, props=props)

        if game_props is None:
            self.game_props = self.mock_necessary_game_props()

        self._user_enter_enabled = True
        self._user_exit_enabled = True
        self.buyin_value = buyin_value

    def mock_necessary_table_props(self) -> dict:
        return {
            "ip": None
        }

    def mock_necessary_game_props(self) -> dict:
        return {
            "blind_small": 10.0,
            "blind_big": 20.0,
            "ante_up": None
        }

    @property
    def user_enter_enabled(self):
        return self._user_enter_enabled

    @property
    def user_exit_enabled(self):
        return self._user_exit_enabled

    async def on_player_enter(self, db, user, seat_idx):
        logger.info("player enter %s -> %s", user.id, seat_idx)
        user.balance = self.buyin_value
        return True

    async def on_player_exit(self, db, user, seat_idx):
        logger.info("player exit %s <- %s", user.id, seat_idx)
        user.balance = 0

    async def user_factory(self, db, user_id, club_id):
        user = User(id=user_id, name='u'+str(user_id))
        #logger.info('user created: %s', user.__dict__)
        return user
    
    async def game_factory(self, users):
        return X_Game(self, users)

