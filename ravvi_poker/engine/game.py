import logging
from enum import Enum

from .cards import Deck
from .events import Message, Command
from .player import Player
from .poker.board import Board, BoardType
from ..db import DBI
from ..logging import ObjectLoggerAdapter

logger = logging.getLogger(__name__)


class GameConditionType(Enum):
    READY = "READY"
    FAST_RECONFIGURE = "FAST_RECONFIGURE"
    FULL_RECONFIGURE = "FULL_RECONFIGURE"


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
        self.boards_types: list[BoardType] | None = None
        self.boards: list[Board] | None = None

        self.condition = self.get_condition()

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

    def get_condition(self) -> GameConditionType:
        """
        Проверяет можно ли игре запускаться в данной конфигурации игроков
        """
        if len(self.players) < (
                players_required := getattr(getattr(self.table, "game_modes_config"), "players_required")):
            return GameConditionType.FULL_RECONFIGURE
        if self.table.TABLE_TYPE == "RG":
            # снимаем флаг is_new_player_on_table, по причине того что у нас минимальное количество участников
            if len(self.players) == players_required and any([p.user.is_new_player_on_table for p in self.players]):
                for p in self.players:
                    p.user.is_new_player_on_table = False
            # если все участники являются новыми, то снимаем флаг is_new_player_on_table
            elif len(self.players) > players_required and all([p.user.is_new_player_on_table for p in self.players]):
                for p in self.players:
                    p.user.is_new_player_on_table = False

            # если на позиции дилера стоит участник с флагом is_new_player_on_table, то требуется быстрая пересборка
            if self.players[0].user.is_new_player_on_table:
                return GameConditionType.FAST_RECONFIGURE

            # проверяем есть ли новые игроки, если да то выбрасываем их из игры если они не в положении большого
            # блайнда
            if any([p.user.is_new_player_on_table for p in self.players]):
                cleared_players_list = []
                for num, p in enumerate(self.players):
                    # TODO игрок может попросить принудительно поставить за него большой блайнд
                    if p.user.is_new_player_on_table and num != 2:
                        continue
                    else:
                        p.user.is_new_player_on_table = False
                        cleared_players_list.append(p)
                self.players = cleared_players_list

        return GameConditionType.READY

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

    def setup_boards(self):
        # deck
        self.deck = Deck(self.GAME_DECK)
        self.get_boards()
        self.boards = [Board(board_type) for board_type in self.boards_types]
        # players
        for p in self.players:
            p.cards = []
            p.cards_open = False

    def get_boards(self):
        self.boards_types = [BoardType.BOARD1]

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
        msg = Message(msg_type=Message.Type.GAME_CARDS, boards=[
            {"board_type": board.board_type.value, "cards": board.cards} for board in self.boards
        ])
        await self.emit_msg(db, msg)

    async def broadcast_PLAYER_CARDS(self, db, player, **kwargs):
        msg = Message(msg_type=Message.Type.PLAYER_CARDS,
                      user_id=player.user_id,
                      cards=player.cards,
                      cards_open=player.cards_open,
                      **kwargs
                      )

        await self.emit_msg(db, msg)

    async def emit_PROPOSED_CARD_DROP(self, db, player, card_code, card_index, **kwargs):
        msg = Message(msg_type=Message.Type.GAME_PROPOSED_CARD_DROP,
                      user_id=player.user_id,
                      card_code=card_code,
                      card_index=card_index,
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

    async def broadcast_ROUND_RESULT(self, db, rewards, banks, bank_total):
        msg = Message(msg_type=Message.Type.ROUND_RESULT, rewards=rewards, banks=banks, bank_total=bank_total)
        await self.emit_msg(db, msg)

    async def broadcast_GAME_RESULT(self, db, balances):
        msg = Message(msg_type=Message.Type.GAME_RESULT, balances=balances)
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
