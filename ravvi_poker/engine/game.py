from ..logging import ObjectLogger
from ..db.adbi import DBI
from .user import User
from .table import Table
from .player import Player
from .event import (
    Event,
    GAME_BEGIN,
    GAME_END,
)

class Game(ObjectLogger):
    DBI = DBI
    GAME_TYPE = None
    GAME_SUBTYPE = None

    def __init__(self, table, users) -> None:
        super().__init__(__name__)
        self.table: Table = table
        self.game_id = None
        self.players = [self.player_factory(u) for u in users]

    def log_prefix(self):
        return f"{self.game_id}:"
    
    def player_factory(self, user):
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
            game_id = self.game_id, 
            game_type = self.game_type,
            game_subtype = self.game_subtype,
            players = [x.user_id for x in self.players],
        )
        return info

    async def broadcast_GAME_BEGIN(self, db):
        game_info = self.get_info()
        event = GAME_BEGIN(**game_info)
        await self.emit_event(db, event)

    async def broadcast_GAME_END(self, db):
        event = GAME_END()
        await self.emit_event(db, event)

    async def emit_event(self, db, event):
        event.update(game_id=self.game_id)
        await self.table.emit_event(db, event)

    @property
    def current_player(self):
        return self.players[0]

    def players_rotate(self, n=1):
        self.players = self.players[n:] + self.players[:n]
        return self.current_player

    async def run(self):
        raise NotImplementedError()

