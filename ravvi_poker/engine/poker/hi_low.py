from itertools import groupby

from ravvi_poker.engine.poker.hands import Hand, LowHand


class HiLowMixin:
    def get_best_hand(self, player_cards, board) -> list[Hand, LowHand | None]:
        print("______________________________________________________")
        print("Вызвали команду получения лучшей руки")
        print(board)
        hi_hand = self.get_best_hand_hi(player_cards, board)
        print(f"Hi Hand {hi_hand}")
        low_hand = self.get_best_hand_low(player_cards, board)
        print(f"Low Hand {low_hand}")
        print("______________________________________________________")

        print(hi_hand, low_hand)
        return [hi_hand, low_hand]

    def get_best_hand_hi(self, player_cards, board) -> Hand:
        return super().get_best_hand(player_cards, board)

    def get_best_hand_low(self, player_cards, board) -> LowHand | None:
        results = []
        for h in self.iter_player_hands_combinations(player_cards, board.cards):
            hand = LowHand(h, board)
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


    def get_winners(self):
        # проверяем есть ли вообще победители по low
        if any([p.hand[1] for p in self.players]):
            # делим каждый банк на две части
            banks = self.split_banks()

            winners = [{}, {}]
            players = [p for p in self.players if p.in_the_game]
            if len(players) == 1:
                p = players[0]
                for num in range(2):
                    w_amount = 0
                    for bank_amount, _ in banks[num]:
                        w_amount += bank_amount
                    winners[num][p.user_id] = w_amount
            else:
                self.handle_high_winners(banks, winners)
                self.handle_low_winners(banks, winners)

                winners_info = [[], []]
                for num in range(2):
                    for p in players:
                        amount = winners[num].get(p.user_id, None)
                        if not amount:
                            continue
                        p.user.balance += amount
                        delta = round(p.balance - p.balance_0, 2)
                        # на первый список победителей не меняем баланс и дельту для фронтенда
                        info = dict(
                            user_id=p.user_id,
                            balance=p.balance,
                            delta=delta
                        )
                        self.log.info("winner: %s %s %s", p.user_id, p.balance, delta)
                        winners_info[num].append(info)

        else:
            # TODO покрыть тестом
            players_hands_copy = {p.user_id: p.hand for p in self.players}
            for p in self.players:
                p.hand = p.hand[0]
            winners_info = super().get_winners()
            for p in self.players:
                p.hand = players_hands_copy[p.user_id]

        return winners_info


    def split_banks(self) -> list:
        banks = [[], []]
        for num in range(len(self.banks)):
            # TODO округление
            banks[0].append(
                (round(self.banks[num][0] / 2, 2), self.banks[num][1]),
            )
            banks[1].append(
                (round(self.banks[num][0] / 2, 2), self.banks[num][1])
            )
        return banks

    def handle_high_winners(self, banks, winners):
        rankKey = lambda x: x.hand[0].rank
        for amount, bank_players in banks[0]:
            bank_players.sort(key=rankKey)
            bank_winners = []
            for _, g in groupby(bank_players, key=rankKey):
                bank_winners = list(g)
            # TODO округление
            w_amount = round(amount / len(bank_winners), 2)
            for p in bank_winners:
                amount = winners[0].get(p.user_id, 0)
                winners[0][p.user_id] = amount + w_amount

    def handle_low_winners(self, banks, winners):
        rankKey = lambda x: x.hand[1].rank if x.hand[1] else (0,)
        for amount, bank_players in banks[1]:
            for p in bank_players:
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                print(p)
                print(p.hand)
                print(p.hand[1])
            bank_players.sort(key=rankKey)
            bank_winners = []
            for _, g in groupby(bank_players, key=rankKey):
                bank_winners = list(g)
            # TODO округление
            w_amount = round(amount / len(bank_winners), 2)
            for p in bank_winners:
                amount = winners[1].get(p.user_id, 0)
                winners[1][p.user_id] = amount + w_amount

    async def open_cards_in_game_end(self, players, open_all):
        best_hand = [None, None]
        async with self.DBI() as db:
            players_to_open_cards = []
            # соберем общий список для открытия карт
            # проходимся по high
            for p in players:
                if not best_hand[0] or best_hand[0].rank <= p.hand[0].rank:
                    best_hand[0] = p.hand[0]
                elif open_all:
                    pass
                else:
                    continue
                if p.cards_open:
                    continue
                p.cards_open = True
                if p not in players_to_open_cards:
                    players_to_open_cards.append(p)

            for p in players:
                # для low руки не обязательно существует ранг
                if (p.hand[1] and not best_hand[1]) or (p.hand[1] and best_hand[1].rank <= p.hand[1].rank):
                    best_hand[1] = p.hand[1]
                else:
                    continue
                if p.cards_open:
                    continue
                p.cards_open = True
                if p not in players_to_open_cards:
                    players_to_open_cards.append(p)

            for p in players_to_open_cards:
                await self.broadcast_PLAYER_CARDS(db, p)
                self.log.info("player %s: open cards %s -> %s, %s", p.user_id, p.cards, p.hand,
                              ",".join([str(hand.type) for hand in p.hand]))

    # async def broadcast_PLAYER_CARDS(self, db, player):
    #     from ravvi_poker.engine.poker.base import PokerBase
    #
    #     self.log.info("Broadcasting Player Cards for HiLow")
    #     hand_type, hand_cards = None, None
    #     print("__________________________-")
    #     print(player.hand)
    #     if player.hand:
    #         hand_type_high = player.hand[0].type[0]
    #         print("!!!!!!!!!!!!")
    #         print(player.hand[1].__dict__ if player.hand[1] is not None else None)
    #         hand_type_low = player.hand[1].type[0] if player.hand[1] is not None else None
    #         high_hand_cards = [c.code for c in player.hand[0].cards]
    #         low_hand_cards = [c.code for c in player.hand[1].cards] if player.hand[1] is not None else []
    #
    #     await super(PokerBase, self).broadcast_PLAYER_CARDS(db, player,
    #                                                         hand_type=[hand_type_high.value, hand_type_low],
    #                                                         hand_cards=[high_hand_cards, low_hand_cards])

    async def broadcast_GAME_RESULT(self, db, winners):
        for winner_message in winners:
            await super().broadcast_GAME_RESULT(db, winner_message)
