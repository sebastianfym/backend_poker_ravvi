import asyncio
import time
from itertools import permutations, combinations
from typing import List, Tuple

from ravvi_poker.engine.poker.double_board import DoubleBoardMixin
from ravvi_poker.engine.poker.bomb_pot import BombPotMixin

from .double_board import MixinMeta
from .hands import HandType, Hand
from .base import PokerBase, Bet, Round
from ..events import Command
from ..user import User
from ...db import DBI


class Poker_NLH_X(PokerBase, metaclass=MixinMeta):
    GAME_TYPE = "NLH"
    GAME_SUBTYPE = None

    PLAYER_CARDS_FREFLOP = 2

    def get_bet_limits(self, player=None):
        p = player or self.current_player
        # TODO округление
        call_delta = max(0, round(self.bet_level - p.bet_amount, 2))
        if self.bet_raise:
            raise_min = round(self.bet_raise + call_delta, 2)
        elif self.bet_level:
            raise_min = round(self.bet_level * 2 - p.bet_amount, 2)
        else:
            raise_min = self.blind_big
        raise_max = p.balance
        return call_delta, raise_min, raise_max, p.balance


class Poker_NLH_REGULAR(Poker_NLH_X):
    GAME_SUBTYPE = "REGULAR"
    GAME_DECK = 52

    SUPPORTED_MODIFICATIONS = [BombPotMixin, DoubleBoardMixin]


class Poker_NLH_AOF(Poker_NLH_X):
    GAME_SUBTYPE = "AOF"
    GAME_DECK = 52

    SUPPORTED_MODIFICATIONS = []

    def __init__(self, table, users: List[User], **kwargs):
        super().__init__(table, users, **kwargs)
        self.ante = None

    def get_bet_options(self, player) -> Tuple[List[Bet], dict]:
        _, _, raise_max, _ = self.get_bet_limits(player)
        options = [Bet.FOLD, Bet.ALLIN]
        params = dict(raise_max=raise_max)
        return options, params

    def handle_bet(self, user_id, bet, raise_delta):
        if bet not in [Bet.FOLD, Bet.ALLIN]:
            bet = Bet.FOLD
        return super().handle_bet(user_id, bet, raise_delta)


class Poker_NLH_3M1(Poker_NLH_X):
    GAME_SUBTYPE = "3-1"
    GAME_DECK = 52

    SUPPORTED_MODIFICATIONS = [BombPotMixin, DoubleBoardMixin]

    PLAYER_CARDS_FREFLOP = 3

    SLEEP_DROP_CARD = 10

    def __init__(self, table, users: List[User], **kwargs):
        super().__init__(table, users, **kwargs)
        if kwargs.get("drop_card_round", None) == "FLOP":
            self.round_to_drop_card: Round = Round.FLOP
        else:
            self.round_to_drop_card: Round = Round.PREFLOP

    async def handle_cmd(self, db, user_id, client_id, cmd_type: Command.Type, props: dict):
        await super().handle_cmd(db, user_id, client_id, cmd_type, props)
        if cmd_type == Command.Type.DROP_CARD:
            await self.handle_cmd_drop_card(db, user_id, client_id, props)

    async def handle_cmd_drop_card(self, db, user_id, client_id, props):
        # TODO проверить а можно ли вообще сбрасывать карту
        await self.drop_card(db, user_id, props.get("card"))

    async def drop_card(self, db, user_id, card_for_drop):
        # удалить карту у пользователя
        for player in self.players:
            if player.user_id == user_id:
                # TODO дописать обработку
                player.cards.remove(card_for_drop)
                # TODO дописать совместимость с double board
                player.hands = [self.get_best_hand(player.cards, board) for board in self.boards]
                # TODO согласовать как мы оповестим о сброшенной карте
                await self.broadcast_PLAYER_CARDS(db, player)

    async def offer_card_for_drop(self, player) -> tuple[int, int]:
        hands_combinations = []
        for board in self.boards:
            for combination in combinations(player.cards, 2):
                if board.cards:
                    combination = combination + tuple(board.cards)
                hand = Hand(combination, board)
                hand.rank = self.get_hand_rank(hand)
                hands_combinations.append(hand)

        hands_combinations.sort(reverse=True, key=lambda x: x.rank)
        card_code_for_drop, card_index_for_drop = None, None
        for num, card in enumerate(player.cards):
            if card not in [hand_card.code for hand_card in hands_combinations[0].cards]:
                card_code_for_drop = card
                card_index_for_drop = num

        return card_code_for_drop, card_index_for_drop

    async def run_round(self, start_from_role):
        async with DBI() as db:
            if self.round is self.round_to_drop_card:
                players_cards_map = {}
                for player in self.players:
                    card_code_for_drop, card_index_for_drop = await self.offer_card_for_drop(player)
                    players_cards_map[player.user_id] = card_code_for_drop

                    await super().emit_PROPOSED_CARD_DROP(db,
                                                          player=player,
                                                          card_code=card_code_for_drop,
                                                          card_index=card_index_for_drop)

                # TODO заменить на проверку что все игроки сбросили карты с таймаутом
                await asyncio.sleep(self.SLEEP_DROP_CARD)

                for player in self.players:
                    if len(player.cards) == self.PLAYER_CARDS_FREFLOP:
                        await self.drop_card(db, player.user_id, players_cards_map[player.user_id])
        await super().run_round(start_from_role)


class Poker_NLH_6P(Poker_NLH_X):
    GAME_SUBTYPE = "6+"
    GAME_DECK = 36

    SUPPORTED_MODIFICATIONS = [BombPotMixin, DoubleBoardMixin]

    GAME_HAND_RANK = [
        HandType.HIGH_CARD,
        HandType.ONE_PAIR,
        HandType.TWO_PAIRS,
        HandType.THREE_OF_KIND,
        HandType.STRAIGHT,
        HandType.FULL_HOUSE,
        HandType.FLUSH,
        HandType.FOUR_OF_KIND,
        HandType.STRAIGHT_FLUSH
    ]

    def __init__(self, table, users: List[User], **kwargs):
        super().__init__(table, users, **kwargs)
        self.ante = None


NLH_GAMES = [
    Poker_NLH_REGULAR,
    Poker_NLH_AOF,
    Poker_NLH_3M1,
    Poker_NLH_6P
]
