from typing import List

from ravvi_poker.engine.poker.hands import Hand, LowHand


class HiLowMixin:
    def get_best_hand(self, player_cards, game_cards) -> list[Hand, LowHand | None]:
        print("______________________________________________________")
        print("Вызвали команду получения лучшей руки")
        hi_hand = self.get_best_hand_hi(player_cards, game_cards)
        print(f"Hi Hand {hi_hand}")
        low_hand = self.get_best_hand_low(player_cards, game_cards)
        print(f"Low Hand {low_hand}")
        print("______________________________________________________")

        print(hi_hand, low_hand)
        return [hi_hand, low_hand]

    def get_best_hand_hi(self, player_cards, game_cards) -> Hand:
        return super().get_best_hand(player_cards, game_cards)

    def get_best_hand_low(self, player_cards, game_cards) -> LowHand | None:
        results = []
        for h in self.iter_player_hands_combinations(player_cards, game_cards):
            hand = LowHand(h)
            hand.rank = self.get_hand_rank(hand)
            results.append(hand)
        print(results)
        print([r.rank for r in results])
        if not results or len(results := [r for r in results if r.rank is not None]) == 0:
            return None


        print(f"Получил руки для low {results}")
        print(results)
        results.sort(reverse=True, key=lambda x: x.rank)
        return results[0]

    async def broadcast_PLAYER_CARDS(self, db, player):
        from ravvi_poker.engine.poker.base import PokerBase

        self.log.info("Broadcasting Player Cards for HiLow")
        hand_type, hand_cards = None, None
        print("__________________________-")
        print(player.hand)
        if player.hand:
            hand_type_high = player.hand[0].type[0]
            print("!!!!!!!!!!!!")
            print(player.hand[1].__dict__ if player.hand[1] is not None else None)
            hand_type_low = player.hand[1].type[0] if player.hand[1] is not None else None
            high_hand_cards = [c.code for c in player.hand[0].cards]
            low_hand_cards = [c.code for c in player.hand[1].cards] if player.hand[1] is not None else []

        await super(PokerBase, self).broadcast_PLAYER_CARDS(db, player,
                                                            hand_type=[hand_type_high.value, hand_type_low],
                                                            hand_cards=[high_hand_cards, low_hand_cards])
