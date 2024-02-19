import time
from typing import List, Tuple, Deque
import asyncio
from itertools import zip_longest, groupby, combinations

from ...logging import getLogger

from .bet import Bet
from .hands import Hand, HandType
from .player import User, Player, PlayerRole
from .multibank import get_banks

from ..game import Game
from ..events import Command

from enum import IntEnum, unique

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
    SLEEP_SHOWDOWN_CARDS = 1.5
    SLEEP_GAME_END = 4

    def __init__(self, table, users: List[User],
                 *, blind_small: float = 0.01, blind_big: float = 0.02, bet_timeout=30,
                 ante: float | None = None, bombpot_blind_multiplier: int | None = None, **kwargs) -> None:
        super().__init__(table=table, users=users)
        self.log.logger = logger
        self.round = None
        self.deck = None
        self.cards = None
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
            cards=self.cards if self.cards else [],
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

    # MSG

    async def broadcast_PLAYER_CARDS(self, db, player):
        hand_type, hand_cards = None, None
        if player.hand:
            hand_type = player.hand.type[0]
            hand_cards = [c.code for c in player.hand.cards]
        await super().broadcast_PLAYER_CARDS(db, player, hand_type=hand_type.value, hand_cards=hand_cards)

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

    def get_best_hand(self, player_cards, game_cards):
        deck36 = (self.GAME_DECK == 36)
        results = []
        for h in self.iter_player_hands_combinations(player_cards, game_cards):
            hand = Hand(h, deck36=deck36)
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

    def get_hand_rank(self, hand):
        if not hand.type:
            return None
        return self.GAME_HAND_RANK.index(hand.type[0]), *hand.type[1:]

    async def run(self):
        self.log.info("begin players: %s", [p.user_id for p in self.players])
        # bank(s)
        self.banks = []
        self.bank_total = 0

        self.setup_players_roles()
        self.setup_cards()

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
        winners_info = self.get_winners()
        async with self.DBI(log=self.log) as db:
            await self.broadcast_GAME_RESULT(db, winners_info)

        # если включен режим seven deuce сформируем новый банк и распределим его
        if self.table.seven_deuce:
            await self.run_SEVEN_DEUCE(winners_info)

        await asyncio.sleep(self.SLEEP_GAME_END)
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
                p.hand = self.get_best_hand(p.cards, self.cards)
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
                p.hand = self.get_best_hand(p.cards, self.cards)
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
                p.hand = self.get_best_hand(p.cards, self.cards)
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
                p.hand = self.get_best_hand(p.cards, self.cards)
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
            p.hand = self.get_best_hand(p.cards, self.cards)
            if isinstance(p.hand, list):
                self.log.info("player %s hand: %s %s", p.user_id, p.hand, ",".join([str(hand.type) for hand in p.hand]))
            else:
                self.log.info("player %s hand: %s %s", p.user_id, p.hand, p.hand.type)
            if p.bet_type == Bet.ALLIN:
                open_all = True
        self.log.info("open all: %s", open_all)

        # open cards
        await self.open_cards_in_game_end(players, open_all)

        await asyncio.sleep(self.SLEEP_ROUND_END)
        self.log.info("SHOWDOWN end")

    async def run_SEVEN_DEUCE(self, winners_info):
        bank_seven_deuce, winners_seven_deuce_info = await self.table.seven_deuce.handle_winners(winners_info,
                                                                                                 self.players)
        if bank_seven_deuce:
            async with self.DBI(log=self.log) as db:
                await self.broadcast_GAME_ROUND_END(db, [bank_seven_deuce], bank_seven_deuce)
                # модификатор не должен перехватить управление (к примеру double board рассчитан список списков,
                # а у нас список словарей
                await super().broadcast_GAME_RESULT(db, winners_seven_deuce_info)

    def append_cards(self, cards_num):
        for _ in range(cards_num):
            self.cards.append(self.deck.get_next())

    async def open_cards_in_game_end(self, players, open_all):
        best_hand = None
        async with self.DBI() as db:
            for p in players:
                if not best_hand or best_hand.rank <= p.hand.rank:
                    best_hand = p.hand
                elif open_all:
                    pass
                else:
                    continue
                if p.cards_open:
                    continue
                p.cards_open = True
                await self.broadcast_PLAYER_CARDS(db, p)
                self.log.info("player %s: open cards %s -> %s, %s", p.user_id, p.cards, p.hand, p.hand.type)

    def get_winners(self):
        winners = {}
        players = [p for p in self.players if p.in_the_game]
        if len(players) == 1:
            p = players[0]
            w_amount = 0
            for bank_amount, _ in self.banks:
                w_amount += bank_amount
            winners[p.user_id] = w_amount
        else:
            rankKey = lambda x: x.hand.rank
            for amount, bank_players in self.banks:
                bank_players.sort(key=rankKey)
                bank_winners = []
                for _, g in groupby(bank_players, key=rankKey):
                    bank_winners = list(g)
                # TODO округление
                w_amount = round(amount / len(bank_winners), 2)
                for p in bank_winners:
                    amount = winners.get(p.user_id, 0)
                    winners[p.user_id] = amount + w_amount
        winners_info = []
        for p in players:
            amount = winners.get(p.user_id, None)
            if not amount:
                continue
            p.user.balance += amount
            # TODO округление
            delta = round(p.balance - p.balance_0, 2)
            info = dict(
                user_id=p.user_id,
                balance=p.balance,
                delta=delta
            )
            self.log.info("winner: %s %s %s", p.user_id, p.balance, delta)
            winners_info.append(info)

        return winners_info

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
