from decimal import Decimal
from enum import IntFlag
from typing import Callable

from ravvi_poker.engine.poker.board import Board
from .bet import Bet
from .hands import Hand, LowHand
from ..player import Player as PlayerBase
from ..user import User


class PlayerRole(IntFlag):
    DEFAULT = 0
    DEALER = 1
    SMALL_BLIND = 2
    BIG_BLIND = 4


class Player(PlayerBase):
    ROLE_DEFAULT = 0
    ROLE_DEALER = 1
    ROLE_SMALL_BLIND = 2
    ROLE_BIG_BLIND = 3

    def __init__(self, user: User) -> None:
        super().__init__(user)
        self.role = Player.ROLE_DEFAULT
        self.hands: list[Hand, LowHand] | None = None
        self.active = True
        self.bet_type = None
        self.bet_amount: Decimal = Decimal("0.00")
        self.bet_ante: Decimal = Decimal("0.00")
        self.bet_delta: Decimal = Decimal("0.00")
        self.bet_total: Decimal = Decimal("0.00")

    @property
    def bet_max(self) -> Decimal:
        return self.bet_amount + self.balance

    @property
    def in_the_game(self) -> bool:
        return self.bet_type != Bet.FOLD

    @property
    def has_bet_opions(self) -> bool:
        return self.in_the_game and self.bet_type != Bet.ALLIN

    def fill_player_hands(self, func_fill: Callable, boards: list[Board]) -> None:
        self.hands = []
        for board in boards:
            if isinstance(result := func_fill(self.cards, board), list):
                # hi-low возвращает сразу две руки
                self.hands.extend(result)
            else:
                self.hands.append(result)
