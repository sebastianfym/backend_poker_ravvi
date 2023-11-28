import logging
from collections import namedtuple

from ravvi_poker.db.dbi import DBI
from ravvi_poker.engine.events import Command, Message

from .x_utils import check_func_args

logger = logging.getLogger(__name__)

class X_DBI:
    _game_id = 1
    _events = list()
    _events_keep = False
    
    GameRow = namedtuple('GameRow', ['id'])

    @classmethod
    def check_methods_compatibility(cls):
        check_func_args(cls.create_game, DBI.create_game)
        check_func_args(cls.close_game, DBI.close_game)
        check_func_args(cls.create_table_msg, DBI.create_table_msg)

    def __init__(self) -> None:
        pass

    async def __aenter__(self):
        if not X_DBI._events_keep:
            X_DBI._events = []
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        pass
    
    async def create_game(self, *, table_id: int, game_type, game_subtype, props, players):
        X_DBI._game_id += 1
        return X_DBI.GameRow(X_DBI._game_id)

    async def close_game(self, id: int, players):
        pass

    async def create_table_msg(self, *, table_id, game_id, msg_type, props, cmd_id=None, client_id=None):
        msg = Message(table_id=table_id, game_id=game_id, msg_type=msg_type, props=props, cmd_id=cmd_id, client_id=client_id)
        logger.debug("table_msg %s", msg)
        X_DBI._events.append(msg)


    @property
    def _event(self):
        return X_DBI._events[-1] if X_DBI._events else None
