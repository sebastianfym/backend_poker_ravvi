from itertools import groupby

from ravvi_poker.engine.poker.board import BoardType


class MixinMeta(type):
    def __call__(cls, *args, **kwargs):
        try:
            mixin = kwargs.pop("mixin")

            # проверяем совместимость модификатора и режима
            if isinstance(mixin, list):
                for mix in mixin:
                    cls.check_compatibility(mix)
            else:
                cls.check_compatibility(mixin)

            # добавляем миксины
            if isinstance(mixin, type):
                name = f"{cls.__name__}With{mixin.__name__}"
                cls = type(name, (mixin, cls), dict(cls.__dict__))
            elif isinstance(mixin, list):
                name = f"{cls.__name__}" + "_".join([f"With{mixin_object.__name__}" for mixin_object in mixin])
                cls = type(name, (*mixin, cls), dict(cls.__dict__))

        except KeyError:
            pass

        return type.__call__(cls, *args, **kwargs)

    def check_compatibility(cls, mixin):
        if mixin not in cls.SUPPORTED_MODIFICATIONS:
            raise ValueError(f"game with type {cls.__name__} not support mode {mixin.__name__}")


class DoubleBoardMixin:
    # TODO понадобится для переписывания на статическое наследование
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.board_types: list[BoardType] = [BoardType.BOARD1, BoardType.BOARD2]

    def get_boards(self):
        self.boards_types = [BoardType.BOARD1, BoardType.BOARD2]

    def get_rounds_results(self) -> list[dict]:
        # делим каждый банк на две части
        banks = [[], []]
        for num in range(len(self.banks)):
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
            for num in range(2):
                w_amount = 0
                for bank_amount, _ in banks[num]:
                    w_amount += bank_amount
                winners[num][p.user_id] = w_amount
        else:
            for num in range(2):
                rankKey = lambda x: x.hands[num].rank
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

        rewards_winners = [[], []]
        rewards = [
            {"type": "board1", "winners": rewards_winners[0]},
            {"type": "board2", "winners": rewards_winners[1]},
        ]
        rounds_results = [
            {
                "rewards": rewards[0],
                "banks": [bank[0] for bank in banks[1]],
                "bank_total": round(sum([bank[0] for bank in banks[1]]), 2)
            },
            {
                "rewards": rewards[1],
                "banks": [],
                "bank_total": 0
            },
        ]
        for p in self.players:
            amount_board_1 = winners[0].get(p.user_id, 0)
            amount_board_2 = winners[1].get(p.user_id, 0)
            if amount_board_1 == 0 and amount_board_2 == 0:
                continue
            p.user.balance += amount_board_1
            if amount_board_1 != 0:
                rewards_winners[0].append(
                    {
                        "user_id": p.user_id,
                        "amount": amount_board_1,
                        "balance": p.user.balance
                    }
                )
            p.user.balance += amount_board_2
            if amount_board_2 != 0:
                rewards_winners[1].append(
                    {
                        "user_id": p.user_id,
                        "amount": amount_board_2,
                        "balance": p.user.balance
                    }
                )
        # TODO это можно перенести в модуль тестов
        [rewards_list["winners"].sort(key=lambda x: x["user_id"]) for rewards_list in rewards]

        return rounds_results

    async def open_cards_in_game_end(self, players, open_all):
        best_hand = [None, None]
        async with self.DBI() as db:
            # соберем общий список для открытия карт
            players_to_open_cards = []
            for num in range(2):
                for p in players:
                    if not best_hand[num] or best_hand[num].rank <= p.hands[num].rank:
                        best_hand[num] = p.hands[num]
                    elif open_all:
                        pass
                    else:
                        continue
                    if p.cards_open:
                        continue
                    p.cards_open = True
                    # TODO эта проверка не нужна
                    if p not in players_to_open_cards:
                        players_to_open_cards.append(p)

            for p in players_to_open_cards:
                await self.broadcast_PLAYER_CARDS(db, p)
                self.log.info("player %s: open cards %s -> %s, %s", p.user_id, p.cards, p.hands,
                              ",".join([str(hand.type) for hand in p.hands]))

# def extend_game_with_double_board(obj):
#     obj.__class__ = type(obj.__class__.__name__, (DoubleBoardMixin, obj.__class__), {})
#
#     return obj
