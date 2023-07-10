from itertools import combinations

from .cards import Hand
from .poker import PokerBase

class Poker_PLO(PokerBase):

    def get_best_hand(self, player_cards, game_cards):
        results = []
        for pc in combinations(player_cards, 2):
            for gc in combinations(game_cards, 3):
                hand = Hand(pc+gc)
                hand.rank = hand.get_rank()
                results.append(hand)
        results.sort(reverse=True, key=lambda x: x.rank)
        return results[0]
