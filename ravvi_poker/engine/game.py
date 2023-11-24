import logging
from ..logging import ObjectLoggerAdapter
from ..db.adbi import DBI

from .cards import get_deck_36, get_deck_52
from .user import User
from .table import Table
from .player import Player
from .events import Message, Command

logger = logging.getLogger(__name__)


class Game:
    DBI = DBI
    GAME_TYPE = None
    GAME_SUBTYPE = None
    GAME_DECK = 52

    def __init__(self, table, game_id, users) -> None:
        self.log = ObjectLoggerAdapter(logger, self, "game_id")
        self.table: Table = table
        self.game_id = game_id
        self.players = [self.player_factory(u) for u in users]
        self.dealer_id = None
        self.deck = None
        self.cards = None

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
            dealer_id = self.dealer_id,
        )
        return info

    # CARDS

    def cards_get_deck(self):
        if self.GAME_DECK==52:
            return get_deck_52() 
        elif self.GAME_DECK==36:
            return get_deck_36()
        raise ValueError(f"Invalid GAME_DECK {self.GAME_DECK}")
            
    def cards_get_next(self):
        return self.deck.pop(0)

    # PLAYERS

    @property
    def current_player(self):
        return self.players[0]

    def players_rotate(self, n=1):
        self.players = self.players[n:] + self.players[:n]
        return self.current_player

    # CMD

    async def handle_cmd(self, db, user_id, client_id, cmd_type: Command.Type, props: dict):
        pass 

    # MSG

    async def broadcast_GAME_BEGIN(self, db):
        game_info = self.get_info()
        msg = Message(msg_type=Message.Type.GAME_BEGIN, props=game_info)
        await self.emit_msg(db, msg)

    async def broadcast_GAME_END(self, db):
        msg = Message(msg_type=Message.Type.GAME_END)
        await self.emit_msg(db, msg)

    async def broadcast_GAME_CARDS(self, db):
        msg = Message(msg_type=Message.Type.GAME_CARDS, cards = self.cards)
        await self.emit_msg(db, msg)

    async def broadcast_PLAYER_CARDS(self, db, player, **kwargs):
        msg = Message(msg_type=Message.Type.PLAYER_CARDS,
            user_id = player.user_id,
            cards = player.cards,
            cards_open = player.cards_open,
            **kwargs
        )
        await self.emit_msg(db, msg)

    async def broadcast_PLAYER_MOVE(self, db, player, **kwargs):
        msg = Message(msg_type=Message.Type.GAME_PLAYER_MOVE, 
            user_id = player.user_id, 
            **kwargs
        )
        await self.emit_msg(db, msg)

    async def broadcast_PLAYER_MOVE(self, db, player, **kwargs):
        msg = Message(msg_type=Message.Type.GAME_PLAYER_MOVE, 
            user_id = player.user_id, 
            **kwargs
        )
        await self.emit_msg(db, msg)

    async def broadcast_PLAYER_BET(self, db, player, **kwargs):
        msg = Message(msg_type=Message.Type.PLAYER_BET,
            user_id = player.user_id,
            **kwargs
        )
        await self.emit_msg(db, msg)

    async def broadcast_GAME_ROUND_END(self, db, banks):
        msg = Message(msg_type=Message.Type.GAME_ROUND, banks = banks)
        await self.emit_msg(db, msg)

    async def broadcast_GAME_RESULT(self, db, winners):
        msg = Message(msg_type=Message.Type.GAME_END, winners=winners)
        await self.emit_msg(db, msg)

    async def broadcast_GAME_END(self, db):
        msg = Message(msg_type=Message.Type.GAME_END)
        await self.emit_msg(db, msg)

    async def emit_msg(self, db, msg):
        msg.update(game_id=self.game_id)
        # TODO
        if self.table:
            await self.table.emit_msg(db, msg)

    async def run(self):
        raise NotImplementedError()
