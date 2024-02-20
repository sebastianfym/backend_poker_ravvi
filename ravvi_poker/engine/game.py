import logging

from .tables.configs import configCls
from ..logging import ObjectLoggerAdapter
from ..db import DBI

from .cards import Deck
from .user import User
from .player import Player
from .events import Message, Command

logger = logging.getLogger(__name__)


class Game:
    DBI = DBI
    GAME_TYPE = None
    GAME_SUBTYPE = None
    GAME_DECK = 52

    def __init__(self, table, users) -> None:
        from .tables import Table

        self.table: Table = table
        self.game_id = None
        self.log = ObjectLoggerAdapter(logger, lambda: self.game_id)
        self.players = [self.player_factory(u) for u in users]
        self.dealer_id = None
        self.deck = None
        self.cards = None

    def player_factory(self, user) -> Player:
        return Player(user)

    @property
    def lock(self):
        return self.table.lock

    @property
    def game_type(self):
        return self.GAME_TYPE

    @property
    def game_subtype(self):
        return self.GAME_SUBTYPE

    @property
    def game_props(self):
        return None

    def get_info(self, users_info: dict = None, user_id: int = None) -> dict:
        info = dict(
            game_id=self.game_id,
            game_type=self.game_type,
            game_subtype=self.game_subtype,
            players=[x.user_id for x in self.players] if self.players is not None else [],
            dealer_id=self.dealer_id,
        )
        return info

    # CARDS

    def setup_cards(self):
        # deck
        self.deck = Deck(self.GAME_DECK)
        self.cards = []
        # players
        for p in self.players:
            p.cards = []
            p.cards_open = False

    # PLAYERS

    @property
    def current_player(self):
        return self.players[0]

    def players_rotate(self, n=1):
        self.players = self.players[n:] + self.players[:n]
        return self.current_player

    # CMD

    async def handle_cmd(self, db, user_id, client_id, cmd_type: Command.Type, props: dict):
        raise NotImplementedError()

    # MSG

    async def broadcast_GAME_BEGIN(self, db):
        game_info = self.get_info()
        msg = Message(msg_type=Message.Type.GAME_BEGIN, **game_info)
        await self.emit_msg(db, msg)

    async def broadcast_GAME_CARDS(self, db):
        msg = Message(msg_type=Message.Type.GAME_CARDS, cards=self.cards)
        await self.emit_msg(db, msg)

    async def broadcast_PLAYER_CARDS(self, db, player, **kwargs):
        msg = Message(msg_type=Message.Type.PLAYER_CARDS,
                      user_id=player.user_id,
                      cards=player.cards,
                      cards_open=player.cards_open,
                      **kwargs
                      )

        await self.emit_msg(db, msg)

    async def broadcast_PLAYER_MOVE(self, db, player, **kwargs):
        msg = Message(msg_type=Message.Type.GAME_PLAYER_MOVE,
                      user_id=player.user_id,
                      **kwargs
                      )
        await self.emit_msg(db, msg)

    async def broadcast_PLAYER_BET(self, db, player, **kwargs):
        msg = Message(msg_type=Message.Type.PLAYER_BET,
                      user_id=player.user_id,
                      **kwargs
                      )
        await self.emit_msg(db, msg)

    async def broadcast_GAME_ROUND_END(self, db, banks, bank_total):
        msg = Message(msg_type=Message.Type.GAME_ROUND, banks=banks, bank_total=bank_total)
        await self.emit_msg(db, msg)

    async def broadcast_GAME_RESULT(self, db, winners):
        msg = Message(msg_type=Message.Type.GAME_RESULT, winners=winners)
        await self.emit_msg(db, msg)

    async def broadcast_GAME_END(self, db):
        msg = Message(msg_type=Message.Type.GAME_END)
        await self.emit_msg(db, msg)

    async def emit_msg(self, db, msg):
        msg.update(game_id=self.game_id)
        if self.table:
            await self.table.emit_msg(db, msg)

    async def run(self):
        raise NotImplementedError()


def get_game_class(game_type, game_subtype):
    from .poker.nlh import NLH_GAMES
    from .poker.plo import PLO_GAMES

    GAME_CLASSES = NLH_GAMES + PLO_GAMES
    GAME_CLASSES_MAP = {(cls.GAME_TYPE, cls.GAME_SUBTYPE): cls for cls in GAME_CLASSES}

    key = (game_type, game_subtype)
    return GAME_CLASSES_MAP.get(key, None)
