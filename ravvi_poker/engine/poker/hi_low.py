from ravvi_poker.engine.poker.hands import Hand


class HiLowMixin:
    def get_best_hand(self, player_cards, game_cards):
        hi_hand = self.get_best_hand_hi(player_cards, game_cards)
        low_hand = self.get_best_hand_low(player_cards, game_cards)

        print(hi_hand)
        print(low_hand)

    def get_best_hand_hi(self, player_cards, game_cards):
        return super().get_best_hand(player_cards, game_cards)

    def get_best_hand_low(self, player_cards, game_cards):
        deck36 = (self.GAME_DECK == 36)
        results = []
        for h in self.iter_player_hands_combinations(player_cards, game_cards):
            hand = Hand(h, deck36=deck36)
            results.append(hand.get_low_type())
        if not results:
            return None
        print(f"Получил руки для low {results}")
        # results.sort(reverse=True, key=lambda x: x.rank)
        return results[0]
