from ..logging import ObjectLogger
from .user import User
from .table import Table
from .player import Player

class Game(ObjectLogger):
    GAME_TYPE = None
    GAME_SUBTYPE = None
    
    def __init__(self, table, users) -> None:
        super().__init__(__name__)
        self.table = table
        self.game_id = None
        self.players = [self.player_factory(u) for u in users]

    def log_prefix(self):
        return f" {self.game_id}: "
    
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
    
    def get_info(self, user_id, users_info=None):
        info = dict(
            game_id = self.game_id, 
            game_type = self.game_type,
            game_subtype = self.game_subtype,
            players = [x.user_id for x in self.players],
        )
        return info


