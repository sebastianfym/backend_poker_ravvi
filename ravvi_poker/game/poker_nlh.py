from itertools import combinations

from .cards import Hand
from .poker import PokerBase


class Poker_NLH(PokerBase):
    PLAYER_CARDS_FREFLOP = 2

    def get_bet_limits(self, player=None):
        p = player or self.current_player
        call_delta = max(0, self.bet_level-p.bet_amount)
        if self.bet_raise:
            raise_min = self.bet_raise + call_delta
        elif self.bet_level:
            raise_min = self.bet_level*2-p.bet_amount
        else:
            raise_min = self.blind_big
        raise_max = p.balance
        return call_delta, raise_min, raise_max

    def get_best_hand(self, player_cards, game_cards):
        results = []
        for h in combinations(player_cards + game_cards, 5):
            hand = Hand(h)
            hand.rank = hand.get_rank()
            results.append(hand)
        results.sort(reverse=True, key=lambda x: x.rank)
        return results[0]
