import asyncio
import time
from enum import IntEnum, unique
from itertools import groupby, combinations
from typing import List, Tuple

from .bet import Bet
from .board import Board, BoardType
from .hands import Hand, HandType, LowHand, LowHandType
from .multibank import get_banks
from .player import User, Player, PlayerRole
from ..events import Command
from ..game import Game
from ...logging import getLogger

logger = getLogger(__name__)


@unique
class Round(IntEnum):
    PREFLOP = 1
    FLOP = 2
    TERN = 3
    RIVER = 4
    SHOWDOWN = 5


class PokerBase(Game):
    PLAYER_CARDS_FREFLOP = 2

    SLEEP_ROUND_BEGIN = 1.5
    SLEEP_ROUND_END = 2
    SLEEP_ROUND_RESULT = 4
    SLEEP_SHOWDOWN_CARDS = 1.5
    SLEEP_GAME_END = 1

    def __init__(self, table, users: List[User],
                 *, blind_small: float = 0.01, blind_big: float = 0.02, bet_timeout=30,
                 ante: float | None = None, bombpot_blind_multiplier: int | None = None, **kwargs) -> None:
        super().__init__(table=table, users=users)
        self.log.logger = logger
        self.round = None
        self.deck = None
        # TODO удалить
        # self.boards_types: list[BoardType] = [BoardType.BOARD1]
        # self.boards = None
        self.bank_total = None
        self.banks = None

        self.blind_small = blind_small
        self.blind_big = blind_big

        # модификаторы
        self.ante = ante
        self.bombpot_blind_multiplier = bombpot_blind_multiplier

        self.bet_id = None
        self.bet_level = 0
        self.bet_raise = 0
        self.bet_total = 0
        self.bet_event = asyncio.Event()
        self.bet_timeout = bet_timeout
        self.bet_timeout_timestamp: int | None = None
        self.count_in_the_game = 0
        self.count_has_options = 0

        self.showdown_is_end: bool = False

    @property
    def game_props(self):
        game_props = dict(
            blind_small=self.blind_small,
            blind_big=self.blind_big,
        )
        if self.ante:
            game_props |= {
                'ante': self.ante
            }

        return game_props

    def player_factory(self, user) -> Player:
        return Player(user)

    def get_info(self, users_info: dict = None, user_id: int = None):
        info = super().get_info()
        info |= self.game_props
        info.update(
            boards=[{
                "board_type": board.board_type.value,
                "cards": board.cards
            } for board in self.boards]
        )
        banks_info = []
        for b in (self.banks or []):
            banks_info.append(b[0])
        info.update(banks=banks_info, bank_total=self.bank_total)
        # current player
        player = self.current_player
        if player.bet_type is None:
            info.update(player_move={
                "user_id": player.user_id,
                "bet_timeout": self.bet_timeout,
                "player_timeout": int(
                    self.bet_timeout_timestamp - time.time()) if self.bet_timeout_timestamp else self.bet_timeout
            })
        if users_info:
            for p in self.players:
                if p.cards_open or p.user_id == user_id:
                    cards = p.cards
                else:
                    cards = [0 for _ in p.cards]
                u = users_info.get(p.user_id, None)
                if not u:
                    continue
                u.update(
                    bet=p.bet_type,
                    amount=p.bet_amount,
                    cards=cards
                )

        return info

    # PLAYERS

    @property
    def current_player(self):
        return self.players[0]

    def players_rotate(self, n=1):
        self.players = self.players[n:] + self.players[:n]
        return self.current_player

    def players_to_role(self, role: PlayerRole):
        for i, p in enumerate(self.players):
            if role in p.role:
                break
        if i == 0:
            return self.current_player
        return self.players_rotate(i)

    # CMD
    async def handle_cmd(self, db, user_id, client_id, cmd_type: Command.Type, props: dict):
        if cmd_type == Command.Type.BET:
            bet_type = props.get("bet", None)
            raise_delta = props.get("amount", None)
            self.handle_cmd_bet(db, user_id=user_id, bet_type=bet_type, raise_delta=raise_delta)
        if cmd_type == Command.Type.SHOW_CARDS:
            cards = props.get("cards", None)
            await self.handle_cmd_show_cards(user_id=user_id, cards=cards)

    # MSG

    async def broadcast_PLAYER_CARDS(self, db, player):
        hands = await self.prepare_hands(player)
        await super().broadcast_PLAYER_CARDS(db, player, hands=hands)

    async def broadcast_PLAYER_CARDS_ON_REQUEST(self, db, player):
        hands = await self.prepare_hands(player)
        visible_cards: list = []
        for card in player.cards:
            if card in player.cards_open_on_request:
                visible_cards.append(card)
            else:
                visible_cards.append(0)
        await super().broadcast_PLAYER_CARDS(db, player, hands=hands, visible_cards=visible_cards)

    async def prepare_hands(self, player) -> list[dict]:
        hands = []
        for player_hand in player.hands:
            hand = {
                "hand_belong": player_hand.board.board_type.value,
            }
            hand_info = {
                "hand_type": player_hand.type[0].value,
                "hand_cards": [c.code for c in player_hand.cards]
            }
            hand |= hand_info
            hands.append(hand)

        return hands

    async def broadcast_PLAYER_MOVE(self, db, player, options, **kwargs):
        await super().broadcast_PLAYER_MOVE(db, player,
                                            options=[int(x) for x in options],
                                            **kwargs
                                            )

    async def broadcast_PLAYER_BET(self, db, player):
        await super().broadcast_PLAYER_BET(db, player,
                                           bet=player.bet_type.value if isinstance(player.bet_type,
                                                                                   Bet) else player.bet_type,
                                           delta=player.bet_delta,
                                           amount=player.bet_amount,
                                           balance=player.balance,
                                           bank_total=self.bank_total
                                           )

    # STATUS

    def update_status(self):
        self.count_in_the_game = 0
        self.count_has_options = 0
        self.bet_level = 0
        self.bet_total = 0

        for p in self.players:
            # self.log.info("%s %s %s ", p.id, p.in_the_game, p.has_bet_opions)
            self.bet_total += p.bet_total
            if not p.in_the_game:
                continue
            self.count_in_the_game += 1
            if p.has_bet_opions:
                self.count_has_options += 1
            if self.bet_level < p.bet_amount:
                self.bet_level = p.bet_amount

        self.log.info(
            f"status: in_the_game:{self.count_in_the_game} has_options:{self.count_has_options} bet_id: {self.bet_id} bet_level:{self.bet_level}")

    # BET

    def get_bet_limits(self, player=None):
        p = player or self.current_player
        call_delta = max(0, self.bet_level - p.bet_amount)
        raise_min = max(call_delta, self.blind_big)
        raise_max = p.balance
        return call_delta, raise_min, raise_max, p.balance

    def get_bet_options(self, player) -> Tuple[List[Bet], dict]:
        call_delta, raise_min, raise_max, player_max = self.get_bet_limits(player)
        options = [Bet.FOLD]
        params = dict()
        if call_delta == 0:
            options.append(Bet.CHECK)
        elif call_delta > 0 and call_delta < player.balance:
            options.append(Bet.CALL)
            params.update(call=call_delta)
        if raise_min < raise_max:
            options.append(Bet.RAISE)
            params.update(raise_min=raise_min, raise_max=raise_max)
        if player_max <= raise_max:
            options.append(Bet.ALLIN)
            params.update(raise_max=raise_max)
        return options, params

    async def player_move(self):
        player = self.current_player
        player.bet_type = None
        options, params = self.get_bet_options(player)
        if player.user.connected:
            self.bet_event.clear()
            async with self.DBI(log=self.log) as db:
                self.bet_timeout_timestamp = int(time.time()) + self.bet_timeout
                await self.broadcast_PLAYER_MOVE(db, player, options, **params,
                                                 bet_timeout=self.bet_timeout, player_timeout=self.bet_timeout)
            self.log.info("wait %ss for player %s ...", self.bet_timeout, player.user_id)
            try:
                await asyncio.wait_for(self.wait_for_player_bet(), self.bet_timeout + 2)
            except asyncio.exceptions.TimeoutError:
                self.log.info("player timeout: %s", player.user_id)
        async with self.DBI() as db:
            if player.bet_type is None:
                if Bet.CHECK in options:
                    self.handle_cmd_bet(db, user_id=player.user_id, bet_type=Bet.CHECK, raise_delta=None)
                else:
                    self.handle_cmd_bet(db, user_id=player.user_id, bet_type=Bet.FOLD, raise_delta=None)
            await self.broadcast_PLAYER_BET(db, player)

    async def wait_for_player_bet(self):
        await self.bet_event.wait()

    def handle_cmd_bet(self, db, *, user_id, bet_type, raise_delta):
        self.log.info("handle_bet: %s %s %s", user_id, bet_type, raise_delta)
        p = self.current_player

        if p.user_id != user_id:
            raise ValueError('invalid user')
        if not Bet.verify(bet_type):
            raise ValueError('invalid bet type')

        b_0, b_a_0, b_t_0 = p.user.balance, p.bet_amount, p.bet_total

        call_delta, raise_min, raise_max, player_max = self.get_bet_limits(p)

        if bet_type == Bet.FOLD:
            p.bet_delta = 0
        elif bet_type == Bet.CHECK:
            if p.bet_amount != self.bet_level:
                raise ValueError(f"player {p.user_id}: bet {p.bet_amount} != current_level {self.bet_level}")
            p.bet_delta = 0
        elif bet_type == Bet.CALL:
            assert call_delta > 0
            p.bet_delta = call_delta
        elif bet_type == Bet.RAISE:
            assert raise_min <= raise_delta and raise_delta <= raise_max
            p.bet_delta = raise_delta
        elif bet_type == Bet.ALLIN:
            p.bet_delta = player_max
        else:
            raise ValueError('invalid bet type')

        p.bet_type = bet_type
        p.bet_amount += p.bet_delta
        p.bet_total += p.bet_delta
        self.bank_total += p.bet_delta
        p.user.balance = round(p.user.balance - p.bet_delta, 2)

        if self.bet_level < p.bet_amount:
            self.bet_id = p.user_id
            self.bet_raise = p.bet_amount - self.bet_level

        self.log.debug("player %s: balance: %s / %s(%s) -> delta: %s -> balance: %s / %s(%s) bet_id: %s",
                       p.user_id, b_0, b_a_0, b_t_0, p.bet_delta, p.balance, p.bet_amount, p.bet_total, self.bet_id)
        self.bet_event.set()

    async def handle_cmd_show_cards(self, user_id, cards):
        self.log.info("handle cmd show_cards: %s %s", user_id, cards)

        for player in self.players:
            # идем дальше только если пришли те карты, которые есть у игрока
            if player.user_id == user_id and set(cards).intersection(set(player.cards)) == set(cards):
                # до shutdown
                # 1. игрок должен быть в состоянии Fold
                # карты для открытия перезаписываются
                if not self.showdown_is_end and not player.in_the_game:
                    player.cards_open_on_request = cards

                # после и во время shutdown
                # 1. карты игрока не открыты принудительно
                # 2. есть еще не открытые карты
                if (not player.cards_open and (not player.cards_open_on_request or
                                               len(player.cards_open_on_request) != len(player.cards))):
                    player.cards_open_on_request = cards
                    if self.showdown_is_end:
                        await self.broadcast_with_db_instance(player)

    async def broadcast_with_db_instance(self, player):
        async with self.DBI() as db:
            await self.broadcast_PLAYER_CARDS_ON_REQUEST(db, player)

    def update_banks(self):
        self.banks, self.bank_total = get_banks(self.players)
        # TODO окргуление
        self.bank_total = round(self.bank_total, 2)
        banks_info = []
        for b in self.banks:
            # TODO окргуление
            banks_info.append(round(b[0], 2))
        # reset bet status
        for p in self.players:
            p.bet_amount = 0
            p.bet_delta = 0
            if p.bet_type in (Bet.FOLD, Bet.ALLIN):
                continue
            p.bet_type = None
        self.bet_level = 0
        self.bet_raise = 0
        return banks_info

    # RUN

    def setup_players_roles(self):
        self.dealer_id = self.players[0].user_id
        if len(self.players) == 2:
            self.players[0].role = PlayerRole.DEALER | PlayerRole.SMALL_BLIND
            self.players[1].role = PlayerRole.BIG_BLIND
            return
        self.players[0].role = PlayerRole.DEALER
        self.players[1].role = PlayerRole.SMALL_BLIND
        self.players[2].role = PlayerRole.BIG_BLIND
        for p in self.players[3:]:
            p.role = PlayerRole.DEFAULT

    async def open_cards(self, db):
        if not (self.count_in_the_game > 1 and self.count_has_options <= 1):
            return
        self.players_to_role(PlayerRole.SMALL_BLIND)
        for p in self.players:
            if p.in_the_game and not p.cards_open:
                p.cards_open = True
                await self.broadcast_PLAYER_CARDS(db, p)
                self.log.info("player %s: open cards %s", p.user_id, p.cards)

    def iter_player_hands_combinations(self, player_cards, game_cards):
        cards = player_cards + game_cards
        return combinations(cards, min(5, len(cards)))

    def get_best_hand(self, player_cards, board: Board) -> Hand | None:
        deck36 = (self.GAME_DECK == 36)
        results = []
        for h in self.iter_player_hands_combinations(player_cards, board.cards):
            hand = Hand(h, board, deck36=deck36)
            hand.rank = self.get_hand_rank(hand)
            results.append(hand)
        if not results:
            return None
        results.sort(reverse=True, key=lambda x: x.rank)
        return results[0]

    GAME_HAND_RANK = [
        HandType.HIGH_CARD,
        HandType.ONE_PAIR,
        HandType.TWO_PAIRS,
        HandType.THREE_OF_KIND,
        HandType.STRAIGHT,
        HandType.FLUSH,
        HandType.FULL_HOUSE,
        HandType.FOUR_OF_KIND,
        HandType.STRAIGHT_FLUSH
    ]

    GAME_LOW_HAND_RANK = [
        LowHandType.H_5432A,
        LowHandType.H_6432A,
        LowHandType.H_6532A,
        LowHandType.H_6542A,
        LowHandType.H_6543A,
        LowHandType.H_65432,
        LowHandType.H_7432A,
        LowHandType.H_7532A,
        LowHandType.H_7542A,
        LowHandType.H_7543A,
        LowHandType.H_75432,
        LowHandType.H_7632A,
        LowHandType.H_7642A,
        LowHandType.H_7643A,
        LowHandType.H_76432,
        LowHandType.H_7652A,
        LowHandType.H_7653A,
        LowHandType.H_76532,
        LowHandType.H_7654A,
        LowHandType.H_76542,
        LowHandType.H_76543,
        LowHandType.H_8432A,
        LowHandType.H_8532A,
        LowHandType.H_8542A,
        LowHandType.H_8543A,
        LowHandType.H_85432,
        LowHandType.H_8632A,
        LowHandType.H_8642A,
        LowHandType.H_8643A,
        LowHandType.H_86432,
        LowHandType.H_8652A,
        LowHandType.H_8653A,
        LowHandType.H_86532,
        LowHandType.H_8654A,
        LowHandType.H_86542,
        LowHandType.H_86543,
        LowHandType.H_8732A,
        LowHandType.H_8742A,
        LowHandType.H_8743A,
        LowHandType.H_87432,
        LowHandType.H_8752A,
        LowHandType.H_8753A,
        LowHandType.H_87532,
        LowHandType.H_8754A,
        LowHandType.H_87542,
        LowHandType.H_87543,
        LowHandType.H_8762A,
        LowHandType.H_8763A,
        LowHandType.H_87632,
        LowHandType.H_8764A,
        LowHandType.H_87642,
        LowHandType.H_87643,
        LowHandType.H_8765A,
        LowHandType.H_87652,
        LowHandType.H_87653,
        LowHandType.H_87654,
    ]

    def get_hand_rank(self, hand):
        print(f"Пришел запрос на get_hand_rank {hand}")
        if not hand.type:
            return None
        if isinstance(hand, LowHand):
            return len(self.GAME_LOW_HAND_RANK) - self.GAME_LOW_HAND_RANK.index(hand.type[0]), *hand.type[1:]
        elif isinstance(hand, Hand):
            return self.GAME_HAND_RANK.index(hand.type[0]), *hand.type[1:]

    async def run(self):
        self.log.info("begin players: %s", [p.user_id for p in self.players])
        # bank(s)
        self.banks = []
        self.bank_total = 0

        self.setup_players_roles()
        self.setup_boards()

        async with self.DBI(log=self.log) as db:
            await self.broadcast_GAME_BEGIN(db)

        if self.ante:
            await self.run_ANTE_COLLECT()
        await self.run_PREFLOP()
        await self.run_FLOP()
        await self.run_TERN()
        await self.run_RIVER()
        await self.run_SHOWDOWN()

        # winners
        rounds_results = self.get_rounds_results()
        for round_result in rounds_results:
            async with self.DBI(log=self.log) as db:
                await self.broadcast_ROUND_RESULT(db, **round_result)
            await asyncio.sleep(self.SLEEP_ROUND_RESULT)

        self.showdown_is_end = True

        # если включен режим seven deuce сформируем новый банк и распределим его
        if self.table.seven_deuce:
            await self.run_SEVEN_DEUCE(rounds_results)

        await self.open_cards_on_request()

        await asyncio.sleep(self.SLEEP_GAME_END)
        async with self.DBI(log=self.log) as db:
            balances = await self.get_balances()
            await self.broadcast_GAME_RESULT(db, balances)
        await asyncio.sleep(0.1)
        async with self.DBI(log=self.log) as db:
            await self.broadcast_GAME_END(db)

        # если включен режим ante_up за столом, то передадим тип последнего раунда в игре, чтобы обработать новое
        # значение анте
        if self.ante:
            await self.table.ante.handle_last_round_type(self.round)

        # если включен режим bombpot, то увеличим счетчик
        if self.table.bombpot:
            await self.table.bombpot.handle_last_round()

        # end
        await asyncio.sleep(0.1)
        self.log.info("end")

    async def run_players_loop(self):
        if self.count_has_options <= 1:
            return
        run_loop = True
        while run_loop:
            player = self.current_player
            if player.has_bet_opions:
                await self.player_move()
                self.update_status()
            if self.count_in_the_game == 1:
                break
            player = self.players_rotate()
            run_loop = player.user_id != self.bet_id

    async def run_round(self, start_from_role):
        if start_from_role:
            self.players_to_role(start_from_role)
        self.players_rotate()
        self.bet_id = self.current_player.user_id
        await self.run_players_loop()

        banks_info = self.update_banks()
        async with self.DBI() as db:
            await self.open_cards(db)
            await self.broadcast_GAME_ROUND_END(db, banks_info, self.bank_total)
        await asyncio.sleep(self.SLEEP_ROUND_END)

    async def run_ANTE_COLLECT(self):
        self.log.info("ANTE COLLECT BEGIN")
        async with self.DBI() as db:
            await self.collect_ante(db)

            banks_info = self.update_banks()
            await self.broadcast_GAME_ROUND_END(db, banks_info, self.bank_total)

    async def run_PREFLOP(self):
        self.log.info("PREFLOP begin")
        self.round = Round.PREFLOP

        self.players_to_role(PlayerRole.DEALER)
        self.players_rotate()
        for _ in range(self.PLAYER_CARDS_FREFLOP):
            for p in self.players:
                p.cards.append(self.deck.get_next())
        self.deck.get_next()

        async with self.DBI() as db:
            for p in self.players:
                p.fill_player_hands(self.get_best_hand, self.boards)
                await self.broadcast_PLAYER_CARDS(db, p)

            self.bet_level = 0

            # small blind
            p = self.players_to_role(PlayerRole.SMALL_BLIND)
            assert PlayerRole.SMALL_BLIND in p.role

            if p.user.balance <= self.blind_small:
                p.bet_type = Bet.ALLIN
                p.bet_delta = p.user.balance
                p.bet_amount = p.user.balance
                p.bet_total += p.user.balance
            else:
                p.bet_type = Bet.SMALL_BLIND
                p.bet_delta = self.blind_small
                p.bet_amount = self.blind_small
                p.bet_total += self.blind_small
            # TODO округление
            self.bank_total = round(self.bank_total + p.bet_delta, 2)
            p.user.balance -= p.bet_delta
            await self.broadcast_PLAYER_BET(db, p)

            # big blind
            p = self.players_to_role(PlayerRole.BIG_BLIND)
            assert PlayerRole.BIG_BLIND in p.role
            if p.user.balance < self.blind_big:
                p.bet_type = Bet.ALLIN
                p.bet_delta = p.user.balance
                p.bet_amount = p.user.balance
                p.bet_total += p.user.balance
            else:
                p.bet_type = Bet.BIG_BLIND
                p.bet_delta = self.blind_big
                p.bet_amount = self.blind_big
                p.bet_total += self.blind_big
            # TODO округление
            self.bank_total = round(self.bank_total + p.bet_delta, 2)
            p.user.balance -= p.bet_delta
            await self.broadcast_PLAYER_BET(db, p)

        # TODO
        self.bet_raise = p.bet_amount - self.bet_level
        self.update_status()

        await self.run_round(None)

        self.log.info("PREFLOP end")

    async def run_FLOP(self):
        if self.count_in_the_game <= 1:
            return
        self.log.info("FLOP begin")
        self.round = Round.FLOP

        self.append_cards(3)
        async with self.DBI() as db:
            await self.broadcast_GAME_CARDS(db)
            self.players_to_role(PlayerRole.DEALER)
            self.players_rotate()
            for p in self.players:
                p.fill_player_hands(self.get_best_hand, self.boards)
                await self.broadcast_PLAYER_CARDS(db, p)

        await self.run_round(PlayerRole.DEALER)
        self.log.info("FLOP end")

    async def run_TERN(self):
        if self.count_in_the_game <= 1:
            return
        self.log.info("TERN begin")
        self.round = Round.TERN

        self.append_cards(1)
        async with self.DBI() as db:
            await self.broadcast_GAME_CARDS(db)
            self.players_to_role(PlayerRole.DEALER)
            self.players_rotate()
            for p in self.players:
                p.fill_player_hands(self.get_best_hand, self.boards)
                await self.broadcast_PLAYER_CARDS(db, p)

        await self.run_round(PlayerRole.DEALER)
        self.log.info("TERN end")

    async def run_RIVER(self):
        if self.count_in_the_game <= 1:
            return
        self.log.info("RIVER begin")
        self.round = Round.RIVER

        self.append_cards(1)
        async with self.DBI() as db:
            await self.broadcast_GAME_CARDS(db)
            self.players_to_role(PlayerRole.DEALER)
            self.players_rotate()
            for p in self.players:
                p.fill_player_hands(self.get_best_hand, self.boards)
                await self.broadcast_PLAYER_CARDS(db, p)

        await self.run_round(PlayerRole.DEALER)
        self.log.info("RIVER end")

    async def run_SHOWDOWN(self):
        if self.count_in_the_game <= 1:
            return
        self.log.info("SHOWDOWN begin")
        self.round = Round.SHOWDOWN

        while self.current_player.user_id != self.bet_id:
            self.players_rotate()

        players = [p for p in self.players if p.in_the_game]
        self.log.info("players in the game: %s", len(players))

        # get players hands
        open_all = False
        for p in players:
            p.fill_player_hands(self.get_best_hand, self.boards)
            self.log.info("player %s hand: %s %s", p.user_id, p.hands, ",".join([str(hand.type) for hand in p.hands
                                                                                 if hand is not None]))
            if p.bet_type == Bet.ALLIN:
                open_all = True
        self.log.info("open all: %s", open_all)

        # open cards
        await self.open_cards_in_game_end(players, open_all)

        await asyncio.sleep(self.SLEEP_ROUND_END)
        self.log.info("SHOWDOWN end")

    async def run_SEVEN_DEUCE(self, rounds_results):
        bank_seven_deuce, round_result = await self.table.seven_deuce.handle_winners(rounds_results,
                                                                                     self.players)
        if bank_seven_deuce:
            async with self.DBI(log=self.log) as db:
                # открываем карты игроков если они выиграли по 7-2 и их карты закрыты
                winners_user_id = [winners["user_id"] for winners in round_result["rewards"]["winners"]]
                for player in self.players:
                    if player.user_id in winners_user_id and not player.cards_open:
                        player.cards_open = True
                        await self.broadcast_PLAYER_CARDS(db, player)
                        await db.commit()

                # отображаем ставки
                for player in self.players:
                    if player.bet_type is Bet.SEVEN_DEUCE:
                        await self.broadcast_PLAYER_BET(db, player)
                        await db.commit()

                await self.broadcast_GAME_ROUND_END(db, [bank_seven_deuce], bank_seven_deuce)
                await db.commit()
                await super().broadcast_ROUND_RESULT(db, **round_result)
                await db.commit()

    def append_cards(self, cards_num):
        for board in self.boards:
            for _ in range(cards_num):
                board.append_card(self.deck.get_next())

    async def open_cards_in_game_end(self, players, open_all):
        best_hand = None
        async with self.DBI() as db:
            for p in players:
                # TODO временно для одной руки
                if not best_hand or best_hand.rank <= p.hands[0].rank:
                    best_hand = p.hands[0]
                elif open_all:
                    pass
                else:
                    continue
                if p.cards_open:
                    continue
                p.cards_open = True
                await self.broadcast_PLAYER_CARDS(db, p)
                # TODO временно для одной руки
                self.log.info("player %s: open cards %s -> %s, %s", p.user_id, p.cards, p.hands, p.hands[0].type)

    async def open_cards_on_request(self):
        print("_______________________")
        print("Прилетел запрос на открытие карт в конце игры")
        # открываем карты по запросу
        async with self.DBI() as db:
            for p in self.players:
                print(f"Смотрим для {p.user_id}")
                print(p.cards_open_on_request)
                print(p.cards_open)
                if p.cards_open_on_request and not p.cards_open:
                    await self.broadcast_PLAYER_CARDS_ON_REQUEST(db, p)
                    self.log.info("player %s: open cards on request %s", p.user_id, p.cards_open_on_request)

    def get_rounds_results(self) -> list[dict]:
        winners = {}
        players = [p for p in self.players if p.in_the_game]
        if len(players) == 1:
            p = players[0]
            w_amount = 0
            for bank_amount, _ in self.banks:
                w_amount += bank_amount
                # TODO округление
            winners[p.user_id] = round(w_amount, 2)
        else:
            rankKey = lambda x: x.hands[0].rank
            for amount, bank_players in self.banks:
                bank_players.sort(key=rankKey)
                bank_winners = []
                for _, g in groupby(bank_players, key=rankKey):
                    bank_winners = list(g)
                # TODO округление
                w_amount = round(amount / len(bank_winners), 2)
                for p in bank_winners:
                    amount = winners.get(p.user_id, 0)
                    # TODO округление
                    winners[p.user_id] = round(amount + w_amount, 2)

        rewards_winners = []
        rewards = {"type": "board1", "winners": rewards_winners}
        rounds_results = [{
            "rewards": rewards,
            "banks": [],
            "bank_total": 0
        }]
        for p in self.players:
            amount = winners.get(p.user_id, None)
            if not amount:
                continue
            # TODO округление
            p.user.balance = round(p.user.balance + amount, 2)
            rewards_winners.append(
                {
                    "user_id": p.user_id,
                    "amount": amount,
                    "balance": p.user.balance
                }
            )
        rewards_winners.sort(key=lambda x: x["user_id"])

        # winners_info = []
        # for p in players:
        #     amount = winners.get(p.user_id, None)
        #     if not amount:
        #         continue
        #     p.user.balance += amount
        #     # TODO округление
        #     delta = round(p.balance - p.balance_0, 2)
        #     info = dict(
        #         user_id=p.user_id,
        #         balance=p.balance,
        #         delta=delta
        #     )
        #     self.log.info("winner: %s %s %s", p.user_id, p.balance, delta)
        #     winners_info.append(info)

        return rounds_results

    async def get_balances(self) -> list[dict]:
        balances = []
        for p in self.players:
            balance = {
                "user_id": p.user_id,
                "balance": p.user.balance,
                "delta": round(p.balance - p.balance_0, 2)
            }
            balances.append(balance)
        # TODO это можно перенести в модуль тестов
        balances.sort(key=lambda x: x["user_id"])
        return balances

    async def collect_ante(self, db):
        for p in self.players:
            if p.balance_0 >= self.ante:
                p.bet_ante = self.ante
            else:
                p.bet_ante = p.balance_0

            p.bet_delta = p.bet_ante
            p.bet_total += p.bet_delta
            # TODO округление
            self.bank_total = round(self.bank_total + p.bet_delta, 2)
            # TODO округление
            p.user.balance = round(p.user.balance - p.bet_delta, 2)
            p.bet_type = Bet.ANTE

            await self.broadcast_PLAYER_BET(db, p)
