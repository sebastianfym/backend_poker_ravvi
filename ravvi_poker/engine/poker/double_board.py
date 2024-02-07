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
        banks_len = len(self.banks)
        for _ in range(banks_len):
            bank = self.banks.pop(0)
            # TODO округление
            self.banks.append(
                (round(bank[0] / 2, 2), bank[1]) * 2
            )

        super().get_winners()

    # async def open_cards_in_game_end(self, players, open_all):
    #     best_hand = None
    #     async with self.DBI() as db:
    #         # соберем общий список для открытия карт
    #         players_to_open_cards = [[], []]
    #         for num in range(2):
    #             for p in players:
    #
    #
    #
    #
    #
    #         for p in players:
    #             if not best_hand or best_hand.rank <= p.hand.rank:
    #                 best_hand = p.hand
    #             elif open_all:
    #                 pass
    #             else:
    #                 continue
    #             if p.cards_open:
    #                 continue
    #             p.cards_open = True
    #             await self.broadcast_PLAYER_CARDS(db, p)
    #             if isinstance(p.hand, list):
    #                 self.log.info("player %s: open cards %s -> %s, %s", p.user_id, p.cards, p.hand,
    #                               ",".join([str(hand.type) for hand in p.hand]))
    #             else:
    #                 self.log.info("player %s: open cards %s -> %s, %s", p.user_id, p.cards, p.hand, p.hand.type)

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

# def extend_game_with_double_board(obj):
#     obj.__class__ = type(obj.__class__.__name__, (DoubleBoardMixin, obj.__class__), {})
#
#     return obj
