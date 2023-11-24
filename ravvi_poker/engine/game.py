import logging
from ..logging import ObjectLoggerAdapter
from ..db.adbi import DBI
from .user import User
from .table import Table
from .player import Player
from .events import Message

logger = logging.getLogger(__name__)


class Game:
    DBI = DBI
    GAME_TYPE = None
    GAME_SUBTYPE = None

    def __init__(self, table, users) -> None:
        self.log = ObjectLoggerAdapter(logger, self, "game_id")
        self.table: Table = table
        self.game_id = None
        self.players = [self.player_factory(u) for u in users]

    def player_factory(self, user) -> Player:
        return Player(user)

    @property
    def game_type(self):
        return self.GAME_TYPE

    @property
    def game_subtype(self):
        return self.GAME_SUBTYPE

    @property
    def game_props(self):
        return None

    def get_info(self, user_id=None, users_info=None):
        info = dict(
            game_id=self.game_id,
            game_type=self.game_type,
            game_subtype=self.game_subtype,
            players=[x.user_id for x in self.players],
        )
        return info

    async def broadcast_GAME_BEGIN(self, db):
        game_info = self.get_info()
        msg = Message(msg_type=Message.Type.GAME_BEGIN, props=game_info)
        await self.emit_msg(db, msg)

    async def broadcast_GAME_END(self, db):
        msg = Message(msg_type=Message.Type.GAME_END)
        await self.emit_msg(db, msg)

    async def emit_msg(self, db, msg):
        msg.update(game_id=self.game_id)
        await self.table.emit_msg(db, msg)

    @property
    def current_player(self):
        return self.players[0]

    def players_rotate(self, n=1):
        self.players = self.players[n:] + self.players[:n]
        return self.current_player

    async def run(self):
        raise NotImplementedError()
