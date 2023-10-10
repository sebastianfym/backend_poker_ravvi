from typing import List, Tuple
from itertools import combinations

from .cards import Hand, CARDS_36
from .poker import PokerBase, Bet


class Poker_NLH_X(PokerBase):
    GAME_TYPE = "NLH"
    GAME_SUBTYPE = None

    PLAYER_CARDS_FREFLOP = 2

    def get_bet_limits(self, player=None):
        p = player or self.current_player
        call_delta = max(0, self.bet_level - p.bet_amount)
        if self.bet_raise:
            raise_min = self.bet_raise + call_delta
        elif self.bet_level:
            raise_min = self.bet_level * 2 - p.bet_amount
        else:
            raise_min = self.blind_big
        raise_max = p.balance
        return call_delta, raise_min, raise_max, p.balance


class Poker_NLH_REGULAR(Poker_NLH_X):
    GAME_TYPE = "NLH"
    GAME_SUBTYPE = "REGULAR"


class Poker_NLH_AOF(Poker_NLH_X):
    GAME_TYPE = "NLH"
    GAME_SUBTYPE = "AOF"

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
    GAME_TYPE = "NLH"
    GAME_SUBTYPE = "3-1"

    PLAYER_CARDS_FREFLOP = 3


class Poker_NLH_6P(Poker_NLH_X):
    GAME_TYPE = "NLH"
    GAME_SUBTYPE = "6+"

    def cards_get_deck(self):
        return CARDS_36()

    def get_best_hand(self, player_cards, game_cards):
        results = []
        for h in combinations(player_cards + game_cards, 5):
            hand = Hand(h)
            hand.rank = hand.get_rank(cards36=True)
            results.append(hand)
        results.sort(reverse=True, key=lambda x: x.rank)
        return results[0]

NLH_subtype_factory = {}
for factory in [Poker_NLH_REGULAR, Poker_NLH_AOF, Poker_NLH_3M1, Poker_NLH_6P]:
    NLH_subtype_factory[factory.GAME_SUBTYPE] = factory