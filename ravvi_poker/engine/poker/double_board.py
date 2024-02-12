from itertools import groupby


class MixinMeta(type):
    def __call__(cls, *args, **kwargs):
        try:
            mixin = kwargs.pop("mixin")
            name = f"{cls.__name__}With{mixin.__name__}"
            cls = type(name, (mixin, cls), dict(cls.__dict__))
        except KeyError:
            pass

        return type.__call__(cls, *args, **kwargs)


class DoubleBoardMixin:
    def setup_cards(self):
        super().setup_cards()
        self.cards = [[], []]

    def append_cards(self, cards_num):
        for num in range(cards_num * 2):
            self.cards[num // cards_num].append(self.deck.get_next())

    def get_best_hand(self, player_cards, game_cards) -> list:
        if len(game_cards) == 0:
            return [super().get_best_hand(player_cards, game_cards), super().get_best_hand(player_cards, game_cards)]
        else:
            return [super().get_best_hand(player_cards, game_cards[0]),
                    super().get_best_hand(player_cards, game_cards[1])]

    def get_winners(self):
        # делим каждый банк на две части
        banks = [[], []]
        for num in range(len(self.banks)):
            print(self.banks[num][0] / 2)
            print(round(self.banks[num][0] / 2, 2))
            # TODO округление
            banks[0].append(
                (round(self.banks[num][0] / 2, 2), self.banks[num][1]),
            )
            banks[1].append(
                (round(self.banks[num][0] / 2, 2), self.banks[num][1])
            )

        winners = [{}, {}]
        players = [p for p in self.players if p.in_the_game]
        if len(players) == 1:
            p = players[0]
            w_amount = 0
            # если один игрок, то нам нет необходимости использовать раздвоенные банки
            for bank_amount, _ in self.banks:
                w_amount += bank_amount
            winners[p.user_id] = w_amount
        else:
            for num in range(2):
                rankKey = lambda x: x.hand[num].rank
                for amount, bank_players in banks[num]:
                    bank_players.sort(key=rankKey)
                    bank_winners = []
                    for _, g in groupby(bank_players, key=rankKey):
                        bank_winners = list(g)
                    # TODO округление
                    w_amount = round(amount / len(bank_winners), 2)
                    for p in bank_winners:
                        amount = winners[num].get(p.user_id, 0)
                        winners[num][p.user_id] = amount + w_amount

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

        return winners_info

    async def open_cards_in_game_end(self, players, open_all):
        best_hand = [None, None]
        async with self.DBI() as db:
            # соберем общий список для открытия карт
            players_to_open_cards = []
            for num in range(2):
                for p in players:
                    if not best_hand[num] or best_hand[num].rank <= p.hand[num].rank:
                        best_hand[num] = p.hand[num]
                    elif open_all:
                        pass
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

    async def broadcast_PLAYER_CARDS(self, db, player):
        from ravvi_poker.engine.poker.base import PokerBase

        self.log.info("Broadcasting Player Cards for Double Board")
        hand_types_list, hand_cards_list = [], []
        if player.hand:
            for hand in player.hand:
                hand_cards_list.append([c.code for c in hand.cards])
                hand_types_list.append(hand.type[0])
        # TODO для PokerBase(PokerClassic работать будет), далее необходимо находить в MRO необходимый класс или
        # TODO задать миксину класс родителя при инициализации
        await super(PokerBase, self).broadcast_PLAYER_CARDS(db, player,
                                                            hand_type=[hand_type.value for hand_type in hand_types_list]
                                                            if len(hand_types_list) != 0 else None,
                                                            hand_cards=[hand_cards for hand_cards in hand_cards_list]
                                                            if len(hand_cards_list) != 0 else None)

    async def broadcast_GAME_RESULT(self, db, winners):
        for winner_message in winners:
            await super().broadcast_GAME_RESULT(db, winner_message)


# def extend_game_with_double_board(obj):
#     obj.__class__ = type(obj.__class__.__name__, (DoubleBoardMixin, obj.__class__), {})
#
#     return obj
