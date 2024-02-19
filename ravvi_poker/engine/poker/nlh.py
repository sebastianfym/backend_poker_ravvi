from typing import List, Tuple

from .double_board import MixinMeta
from .hands import HandType
from .base import PokerBase, Bet
from ..user import User


class Poker_NLH_X(PokerBase, metaclass=MixinMeta):
    GAME_TYPE = "NLH"
    GAME_SUBTYPE = None

    PLAYER_CARDS_FREFLOP = 2

    def get_bet_limits(self, player=None):
        p = player or self.current_player
        # TODO округление
        call_delta = max(0, round(self.bet_level - p.bet_amount, 2))
        if self.bet_raise:
            raise_min = round(self.bet_raise + call_delta, 2)
        elif self.bet_level:
            raise_min = round(self.bet_level * 2 - p.bet_amount, 2)
        else:
            raise_min = self.blind_big
        raise_max = p.balance
        return call_delta, raise_min, raise_max, p.balance


class Poker_NLH_REGULAR(Poker_NLH_X):
    GAME_SUBTYPE = "REGULAR"
    GAME_DECK = 52



class Poker_NLH_AOF(Poker_NLH_X):
    GAME_SUBTYPE = "AOF"
    GAME_DECK = 52

    def __init__(self, table, users: List[User], **kwargs):
        super().__init__(table, users, **kwargs)
        self.ante = None

    def get_bet_options(self, player) -> Tuple[List[Bet], dict]:
        _, _, raise_max, _ = self.get_bet_limits(player)
        options = [Bet.FOLD, Bet.ALLIN]
        params = dict(raise_max=raise_max)
        return options, params

    def handle_bet(self, user_id, bet, raise_delta):
        if bet not in [Bet.FOLD, Bet.ALLIN]:
            bet = Bet.FOLD
        return super().handle_bet(user_id, bet, raise_delta)


class Poker_NLH_3M1(Poker_NLH_X):
    GAME_SUBTYPE = "3-1"
    GAME_DECK = 52

    PLAYER_CARDS_FREFLOP = 3



class Poker_NLH_6P(Poker_NLH_X):
    GAME_SUBTYPE = "6+"
    GAME_DECK = 36

    GAME_HAND_RANK = [
        HandType.HIGH_CARD, 
        HandType.ONE_PAIR,
        HandType.TWO_PAIRS,
        HandType.THREE_OF_KIND,
        HandType.STRAIGHT,
        HandType.FULL_HOUSE,
        HandType.FLUSH,
        HandType.FOUR_OF_KIND,
        HandType.STRAIGHT_FLUSH
    ]

    def __init__(self, table, users: List[User], **kwargs):
        super().__init__(table, users, **kwargs)
        self.ante = None

NLH_GAMES = [
    Poker_NLH_REGULAR,
    Poker_NLH_AOF,
    Poker_NLH_3M1,
    Poker_NLH_6P
]

