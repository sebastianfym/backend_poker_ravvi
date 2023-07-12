from itertools import combinations

from .cards import Hand
from .poker import PokerBase

class Poker_NLH(PokerBase):

    def get_best_hand(self, player_cards, game_cards):
        results = []
        for h in combinations(player_cards+game_cards, 5):
            hand = Hand(h)
            hand.rank = hand.get_rank()
            results.append(hand)
        results.sort(reverse=True, key=lambda x: x.rank)
        return results[0]
