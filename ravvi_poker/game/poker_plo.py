from itertools import combinations

from .cards import Hand
from .poker import PokerBase


class Poker_PLO_X(PokerBase):
    def get_bet_limits(self, player=None):
        p = player or self.current_player
        call_delta = max(0, self.bet_level - p.bet_amount)
        #raise_min = max(p.bet_amount + call_delta + self.bet_raise, self.blind_big)
        if self.bet_raise:
            raise_min = self.bet_raise + call_delta
        elif self.bet_level:
            raise_min = self.bet_level*2-p.bet_amount
        else:
            raise_min = self.blind_big
        raise_max = min(self.bet_total + call_delta*2, p.balance)
        return call_delta, raise_min, raise_max

    def get_best_hand(self, player_cards, game_cards):
        results = []
        for pc in combinations(player_cards, 2):
            for gc in combinations(game_cards, 3):
                hand = Hand(pc + gc)
                hand.rank = hand.get_rank()
                results.append(hand)
        results.sort(reverse=True, key=lambda x: x.rank)
        return results[0]


class Poker_PLO_4(Poker_PLO_X):
    PLAYER_CARDS_FREFLOP = 4


class Poker_PLO_5(Poker_PLO_X):
    PLAYER_CARDS_FREFLOP = 5


class Poker_PLO_6(Poker_PLO_X):
    PLAYER_CARDS_FREFLOP = 6
