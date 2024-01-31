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
    async def run_FLOP(self):
        from ravvi_poker.engine.poker.player import PlayerRole

        self.log.info("FLOP with DoubleBoard begin")

        print(self.count_in_the_game)
        if self.count_in_the_game <= 1:
            return

        self.cards = [[], []]
        for num in range(6):
            self.cards[num // 3].append(self.deck.get_next())
        async with self.DBI() as db:
            await self.broadcast_GAME_CARDS(db)
            self.players_to_role(PlayerRole.DEALER)
            self.players_rotate()
            for p in self.players:
                p.hand = self.get_best_hand(p.cards, self.cards[0])
                await self.broadcast_PLAYER_CARDS(db, p)

        await self.run_round(PlayerRole.DEALER)
        self.log.info("FLOP with DoubleBoard end")

    def get_best_hand(self, cards):
        # Обрабатываем руку для двух колод
        pass

    async def broadcast_PLAYER_CARDS(self, db, player):
        # Броадкастим две руки
        pass


# def extend_game_with_double_board(obj):
#     obj.__class__ = type(obj.__class__.__name__, (DoubleBoardMixin, obj.__class__), {})
#
#     return obj
