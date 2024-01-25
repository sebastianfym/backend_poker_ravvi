import logging

from .tables.configs import configCls
from ..logging import ObjectLoggerAdapter
from ..db import DBI

from .cards import Deck
from .user import User
from .tables import Table
from .player import Player
from .events import Message, Command

logger = logging.getLogger(__name__)


class Game:
    DBI = DBI
    GAME_TYPE = None
    GAME_SUBTYPE = None
    GAME_DECK = 52

    def __init__(self, table, users) -> None:
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

    def get_info(self, users_info: dict) -> dict:
        return self.get_info_before_game_start(self.table, users_info)

    @staticmethod
    def get_info_before_game_start(table: Table, users_info: dict) -> dict:
        info = dict(
            game_id=None,
            game_type=table.game_type,
            game_subtype=table.game_subtype,
            users=list(users_info.values()),
            players=list(users_info.keys()),
            blinds={
                "blind_small": table.game_props["blind_value"],
                "blind_big": table.game_props["blind_value"] * 2,
            }
        )
        # добавляем анте
        if table.game_props["ante_up"]:
            info |= {
                "ante": table.game_props["ante_levels"],
                "current_ante": table.game_props["ante_levels"][0]
            }
        # добавляем данные из конфиг классов
        for configCl in configCls:
            if len(config_dict_for_add := table.__dict__[configCl.cls_as_config_name()].unpack_for_msg()) != 0:
                info |= config_dict_for_add
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
        users_info = {u.id: u.get_info() for u in self.table.seats if u is not None}
        game_info = self.get_info(users_info)
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

    async def broadcast_GAME_ROUND_END(self, db, banks):
        msg = Message(msg_type=Message.Type.GAME_ROUND, banks=banks)
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
