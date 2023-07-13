from typing import List, Tuple
import random
import asyncio
from itertools import zip_longest, groupby, combinations

from ..logging import ObjectLogger
from .bet import Bet
from .event import Event, GAME_BEGIN, PLAYER_CARDS, GAME_CARDS, PLAYER_BET, GAME_PLAYER_MOVE, GAME_ROUND, GAME_RESULT, GAME_END
from .player import User, Player, PlayerRole
from .cards import Hand, HandRank
from .multibank import get_banks

from enum import IntEnum, unique

@unique
class Round(IntEnum):
    PREFLOP = 1
    FLOP = 2
    TERN = 3
    RIVER = 4

class PokerBase(ObjectLogger):

    PLAYER_CARDS_FREFLOP = 2

    SLEEP_ROUND_BEGIN = 1.5
    SLEEP_ROUND_END = 1.5
    SLEEP_SHOWDOWN_CARDS = 1.5
    SLEEP_GAME_END = 3

    def __init__(self, table, game_id, users: List[User]) -> None:
        super().__init__(__name__+f".{game_id}")
        self.table = table
        self.game_id = game_id
        self.round = None
        self.players = [Player(u) for u in users]
        self.dealer_id = None
        self.deck = None
        self.cards = None
        self.banks = None

        self.blind_small = 1
        self.blind_big = 2

        self.bet_id = None
        self.bet_level = 0
        self.bet_raise = 0
        self.bet_total = 0
        self.bet_event = asyncio.Event()
        self.bet_timeout = 30
        self.count_in_the_game = 0
        self.count_has_options = 0

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
        if i==0:
            return self.current_player
        return self.players_rotate(i)

    # CARDS

    def cards_get_next(self):
        return self.deck.pop(0)

    # EVENTS

    async def broadcast(self, event: Event):
        if self.table:
            await self.table.broadcast(event)

    async def broadcast_GAME_BEGIN(self):
        event = GAME_BEGIN(
            game_id = self.game_id, 
            players = [x.user_id for x in self.players],
            dealer_id = self.dealer_id
        )
        await self.broadcast(event)

    async def broadcast_PLAYER_CARDS(self, player):
        event = PLAYER_CARDS(
            user_id = player.user_id,
            cards = player.cards,
            cards_open = player.cards_open
        )
        await self.broadcast(event)

    async def broadcast_GAME_CARDS(self):
        event = GAME_CARDS(
            cards = self.cards
        )
        await self.broadcast(event)
       
    async def broadcast_PLAYER_MOVE(self):
        player = self.current_player
        options, params = self.get_bet_options(player)
        event = GAME_PLAYER_MOVE(
            user_id = player.user_id,
            options = options, 
            **params
        )
        await self.broadcast(event)

    async def broadcast_PLAYER_BET(self):
        player = self.current_player
        event = PLAYER_BET(
            user_id = player.user_id,
            bet = player.bet_type,
            delta = player.bet_delta,
            amount = player.bet_amount,
            balance = player.balance
        )
        await self.broadcast(event)

    async def broadcast_GAME_ROUND_END(self, banks_info):
        event = GAME_ROUND(banks = banks_info)
        await self.broadcast(event)

    # STATUS

    def update_status(self):
        self.count_in_the_game = 0
        self.count_has_options = 0
        self.bet_level = 0
        self.bet_total = 0

        for p in self.players:
            self.bet_total += p.bet_total
            if not p.in_the_game:
                continue
            self.count_in_the_game += 1
            if p.has_bet_opions:
                self.count_has_options += 1
            if self.bet_level<p.bet_amount:
                self.bet_level = p.bet_amount
        self.log_info(f"status: in_the_game:{self.count_in_the_game} has_options:{self.count_has_options} bet_id: {self.bet_id} bet_level:{self.bet_level}")

    # BET

    def get_bet_limits(self, player=None):
        p = player or self.current_player
        call_delta = max(0, self.bet_level-p.bet_amount)
        raise_min = self.bet_level + self.blind_big
        raise_max = p.bet_amount + p.balance
        return call_delta, raise_min, raise_max

    def get_bet_options(self, player) -> Tuple[List[Bet], dict]:
        call_delta, raise_min, raise_max = self.get_bet_limits(player)
        options = [Bet.FOLD]
        params = dict()
        if call_delta==0:
            options.append(Bet.CHECK)
        elif call_delta>0 and call_delta<player.balance:
            options.append(Bet.CALL)
            params.update(call=call_delta)
        if raise_min<raise_max:
            options.append(Bet.RAISE)
            params.update(raise_min = raise_min, raise_max = raise_max)
        player_max = player.bet_amount+player.balance
        if player_max<=raise_max:
            options.append(Bet.ALLIN)
            params.update(raise_max=raise_max)
        return options, params
    
    async def player_move(self):
        player = self.current_player
        player.bet_type = None
        await self.broadcast_PLAYER_MOVE()
        try:
            self.bet_event.clear()
            self.log_info("wait (%ss) for player %s ...", self.bet_timeout, player.user_id)
            await asyncio.wait_for(self.wait_for_player_bet(), self.bet_timeout)
        except asyncio.exceptions.TimeoutError:
            self.log_info("player timeout: %s", player.user_id)
        if player.bet_type is None:
            player.bet_type = Bet.FOLD
            player.bet_delta = 0
        await self.broadcast_PLAYER_BET()

    async def wait_for_player_bet(self):
        await self.bet_event.wait()

    def handle_bet(self, user_id, bet, amount):
        self.log_info("handle_bet: %s %s %s", user_id, bet, amount)
        p = self.current_player
        assert p.user_id == user_id
        assert Bet.verify(bet)

        b_0, b_a_0, b_t_0 = p.user.balance, p.bet_amount, p.bet_total

        call_delta, raise_min, raise_max = self.get_bet_limits(p)

        if bet == Bet.FOLD:
            p.bet_delta = 0
        elif bet == Bet.CHECK:
            if p.bet_amount!=self.bet_level:
                raise ValueError(f"player {p.user_id}: bet {p.bet_amount} != current_level {self.bet_level}")
            p.bet_delta = 0
        elif bet == Bet.CALL:
            assert call_delta>0
            p.bet_delta = call_delta
        elif bet == Bet.RAISE:
            assert raise_min<=amount and amount<=raise_max
            p.bet_delta = amount-p.bet_amount
        elif bet == Bet.ALLIN:
            p.bet_delta = p.balance
        else:
            raise ValueError('inalid bet type')

        p.bet_type = bet
        p.bet_amount += p.bet_delta
        p.bet_total += p.bet_delta
        p.user.balance -= p.bet_delta

        if self.bet_level<p.bet_amount:
            self.bet_id = p.user_id
            self.bet_raise = p.bet_amount-self.bet_level

        self.log_debug("player %s: balance: %s / %s(%s) -> delta: %s -> balance: %s / %s(%s) bet_id: %s", 
                       p.user_id, b_0, b_a_0, b_t_0, p.bet_delta, p.balance, p.bet_amount, p.bet_total, self.bet_id)
        self.bet_event.set()

    def update_banks(self):
        prev_banks = self.banks or []
        self.banks = get_banks(self.players)
        banks_info = []
        for pb, nb in zip_longest(prev_banks, self.banks):
            pb = pb or (0, [])
            info = dict(amount = nb[0], delta = nb[0]-pb[0])
            banks_info.append(info)

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
        if len(self.players)==2:
            self.players[0].role = PlayerRole.DEALER | PlayerRole.SMALL_BLIND
            self.players[1].role = PlayerRole.BIG_BLIND
            return
        self.players[0].role = PlayerRole.DEALER
        self.players[1].role = PlayerRole.SMALL_BLIND
        self.players[2].role = PlayerRole.BIG_BLIND
        for p in self.players[3:]:
            p.role = PlayerRole.DEFAULT

    def setup_cards(self):
        # deck
        self.deck = list(range(1,53))
        random.shuffle(self.deck)
        self.cards = []
        # players
        for p in self.players:
            p.cards = []
            p.cards_open = False


    async def open_cards(self):
        if not (self.count_in_the_game>1 and self.count_has_options<=1):
            return
        self.players_to_role(PlayerRole.SMALL_BLIND)
        for p in self.players:
            if p.in_the_game and not p.cards_open:
                p.cards_open = True
                await self.broadcast_PLAYER_CARDS(p)
                self.log_info("player %s: open cards %s", p.user_id, p.cards)

    def get_best_hand(self, player_cards, game_cards):
        cards = player_cards+game_cards
        results = []
        for h in combinations(cards, 5):
            hand = Hand(h)
            hand.rank = hand.get_rank()
            results.append(hand)
        results.sort(reverse=True, key=lambda x: x.rank)
        return results[0]

    async def run(self):
        self.log_info("begin players: %s", [p.user_id for p in self.players])
        self.setup_players_roles()
        self.setup_cards()

        await self.broadcast_GAME_BEGIN()

        await self.run_PREFLOP()
        await self.run_FLOP()
        await self.run_TERN()
        await self.run_RIVER()
        await self.run_SHOWDOWN()

        # winners
        winners_info = self.get_winners()

        event = GAME_RESULT(winners=winners_info)
        await self.broadcast(event)

        await asyncio.sleep(self.SLEEP_GAME_END)
        
        event = GAME_END()
        await self.broadcast(event)

        # end
        self.log_info("end")

    async def run_players_loop(self):
        if self.count_has_options<=1:
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

    async def run_round(self, start_from_role, loop_callback=None):
        if start_from_role:
            self.players_to_role(start_from_role)
        self.players_rotate()
        self.bet_id = self.current_player.user_id
        await self.run_players_loop()
        await self.open_cards()

        banks_info = self.update_banks()
        await self.broadcast_GAME_ROUND_END(banks_info)        
        await asyncio.sleep(self.SLEEP_ROUND_END)

    async def run_PREFLOP(self):
        self.log_info("PREFLOP begin")

        self.players_to_role(PlayerRole.DEALER)
        self.players_rotate()
        for _ in range(self.PLAYER_CARDS_FREFLOP):
            for p in self.players:
                p.cards.append(self.cards_get_next())
        self.cards_get_next()
        for p in self.players:
            await self.broadcast_PLAYER_CARDS(p)

        self.bet_level = 0

        # small blind
        p = self.players_to_role(PlayerRole.SMALL_BLIND)
        assert PlayerRole.SMALL_BLIND in p.role 
        p.bet_type = Bet.SMALL_BLIND
        p.bet_delta = self.blind_small
        p.bet_amount += p.bet_delta
        p.bet_total += p.bet_delta
        p.user.balance -= p.bet_delta
        await self.broadcast_PLAYER_BET()
        
        # big blind
        p = self.players_to_role(PlayerRole.BIG_BLIND)
        assert PlayerRole.BIG_BLIND in p.role 
        p.bet_type = Bet.BIG_BLIND
        p.bet_delta = self.blind_big
        p.bet_amount += p.bet_delta
        p.bet_total += p.bet_delta
        p.user.balance -= p.bet_delta
        await self.broadcast_PLAYER_BET()

        self.bet_raise = p.bet_amount-self.bet_level
        self.update_status()        
        
        await self.run_round(None)

        self.log_info("PREFLOP end")

    async def run_FLOP(self):
        if self.count_in_the_game<=1:
            return
        self.log_info("FLOP begin")

        for _ in range(3):
            self.cards.append(self.cards_get_next())
        await self.broadcast_GAME_CARDS()

        await self.run_round(PlayerRole.DEALER)
        self.log_info("FLOP end")

    async def run_TERN(self):
        if self.count_in_the_game<=1:
            return
        self.log_info("TERN begin")

        for _ in range(1):
            self.cards.append(self.cards_get_next())
        await self.broadcast_GAME_CARDS()

        await self.run_round(PlayerRole.DEALER)
        self.log_info("TERN end")

    async def run_RIVER(self):
        if self.count_in_the_game<=1:
            return
        self.log_info("RIVER begin")

        for _ in range(1):
            self.cards.append(self.cards_get_next())
        await self.broadcast_GAME_CARDS()

        await self.run_round(PlayerRole.DEALER)
        self.log_info("RIVER end")

    async def run_SHOWDOWN(self):
        if self.count_in_the_game<=1:
            return
        self.log_info("SHOWDOWN begin")

        while self.current_player.user_id != self.bet_id:
            self.players_rotate()

        players = [p for p in self.players if p.in_the_game]
        self.log_info("players in the game: %s", len(players))

        # get playes hands
        open_all = False
        for p in players:
            p.hand = self.get_best_hand(p.cards, self.cards)
            self.log_info("player %s hand: %s %s", p.user_id, p.hand, p.hand.rank)
            if p.bet_type==Bet.ALLIN:
                open_all = True
        self.log_info("open all: %s", open_all)

        # open cards
        best_hand = None
        for p in players:
            if not best_hand or best_hand.rank<=p.hand.rank:
                best_hand = p.hand
            elif open_all:
                pass
            else:
                continue
            if p.cards_open:
                continue
            p.cards_open = True
            await self.broadcast_PLAYER_CARDS(p)
            self.log_info("player %s: open cards %s -> %s, %s", p.user_id, p.cards, p.hand, p.hand.rank)
            if not open_all:
                await asyncio.sleep(self.SLEEP_SHOWDOWN_CARDS)
        
        await asyncio.sleep(self.SLEEP_ROUND_END)
        self.log_info("SHOWDOWN end")

    def get_winners(self):
        winners = {}
        players = [p for p in self.players if p.in_the_game]
        if len(players)==1:
            p = players[0]
            w_amount = 0
            for bank_amount, _ in self.banks:
                w_amount += bank_amount
            winners[p.user_id] = w_amount
        else:
            rankKey = lambda x: x.hand.rank if x.hand else HandRank.EMPTY
            for amount, bank_players in self.banks:
                bank_players.sort(key=rankKey)
                bank_winners = []
                for _, g in groupby(bank_players, key=rankKey):
                    bank_winners = list(g)
                w_amount = int(amount/len(bank_winners))
                for p in bank_winners:
                    amount = winners.get(p.user_id, 0)
                    winners[p.user_id] = amount + w_amount
        winners_info = []
        for p in players:
            amount = winners.get(p.user_id, None)
            if not amount:
                continue
            p.user.balance += amount
            delta = p.balance - p.balance_0
            info = dict(
                user_id = p.user_id,
                balance = p.balance,
                delta = delta
            )
            self.log_info("winner: %s %s %s", p.user_id, p.balance, delta)
            winners_info.append(info)
        
        return winners_info



