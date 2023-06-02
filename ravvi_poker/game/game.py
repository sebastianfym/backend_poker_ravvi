from typing import List, Tuple
import logging
import time
import random
import asyncio

from ..logging import ObjectLogger
from .bet import Bet
from .event import Event, GAME_BEGIN, PLAYER_CARDS, GAME_CARDS, PLAYER_BET, GAME_PLAYER_MOVE, GAME_ROUND, GAME_END
from .player import Player, User
from .cards import get_player_best_hand

from enum import IntEnum, unique

@unique
class Round(IntEnum):    
    PREFLOP = 1
    FLOP = 2
    TERN = 3
    RIVER = 4

class Game(ObjectLogger):

    SLEEP_ROUND_BEGIN = 1.5
    SLEEP_ROUND_END = 1.5
    SLEEP_SHOWDOWN_CARDS = 1.5
    SLEEP_GAME_END = 1.5

    def __init__(self, table, game_id, users: List[User], *, deck=None) -> None:
        super().__init__(__name__+f".{game_id}")
        self.table = table
        self.game_id = game_id
        self.round = None
        self.players = [Player(u) for u in users]
        self.dealer_id = self.players[0].user_id
        self.count_in_the_game = 0
        self.count_has_options = 0
        self.bet_id = None
        self.bet_level = 0
        self.bets_all_same = False
        self.bank = 0
        self.wait_timeout = 60
        if deck:
            self.deck = list(reversed(deck))
        else:
            self.deck = list(range(1,53))
            random.shuffle(self.deck)
        self.cards = None

        self.bet_event = asyncio.Event()

    @property
    def current_player(self):
        return self.players[0]
    
    async def run(self):
        self.log_info("begin players: %s", [p.user_id for p in self.players])
        await self.on_begin()
        while await self.run_step():
            pass
        await self.on_end()
        self.log_info("end")

    async def on_begin(self):
        assert self.round is None
        # cards
        self.cards = []
        # roles
        if len(self.players)>2:
            self.players[0].role = Player.ROLE_DEALER
            self.players[1].role = Player.ROLE_SMALL_BLIND
            self.players[2].role = Player.ROLE_BIG_BLIND
        else:
            self.players[0].role = Player.ROLE_SMALL_BLIND
            self.players[1].role = Player.ROLE_BIG_BLIND

        await self.broadcast_GAME_BEGIN()
        await self.round_begin(Round.PREFLOP)

        self.update_status()        

    async def run_step(self):
        player = self.current_player

        if player.has_bet_opions:
            await self.player_move()
            self.update_status()

        if self.count_in_the_game == 1:
            await self.round_end()
            return False

        player = self.rotate_players()
        if self.round == Round.PREFLOP:
            if player.user_id == self.bet_id and self.bets_all_same:
                await self.round_end()
                await self.round_begin(Round.FLOP)
                if self.count_has_options>1:
                    return True
        player = self.current_player
        if self.round == Round.FLOP:
            if player.user_id == self.bet_id:
                await self.round_end()
                await self.round_begin(Round.TERN)
                if self.count_has_options>1:
                    return True
        player = self.current_player
        if self.round == Round.TERN:
            if player.user_id == self.bet_id:
                await self.round_end()
                await self.round_begin(Round.RIVER)
                if self.count_has_options>1:
                    return True
        player = self.current_player
        if self.round == Round.RIVER:
            if player.user_id == self.bet_id:
                await self.round_end()
                return False

        return True
    
    
    def update_status(self):
        self.count_in_the_game = 0
        self.count_has_options = 0
        self.bet_level = None
        self.bets_all_same = True

        for p in self.players:
            if not p.in_the_game:
                continue
            self.count_in_the_game += 1
            if p.has_bet_opions:
                self.count_has_options += 1
            if self.bet_level is None:
                self.bet_level = p.bet_amount
            if self.bet_level<p.bet_amount:
                self.bet_level = p.bet_amount
                if p.bet_type != Bet.ALLIN:
                    self.bets_all_same = False
        self.log_info(f"status: in_the_game:{self.count_in_the_game} has_options:{self.count_has_options} bet_id: {self.bet_id} bet_level:{self.bet_level} bets_all_same:{self.bets_all_same}")
    
    def get_bet_limits(self, player=None, BB=2):
        p = player or self.current_player
        call_delta = max(0, self.bet_level-p.bet_amount)
        if self.count_has_options>2:
            raise_min = call_delta + BB
        else:
            raise_min = call_delta + max(BB, call_delta)
        raise_max = p.balance
        return call_delta, raise_min, raise_max

    def get_bet_options(self, player) -> Tuple[List[Bet], dict]:
        call_delta, raise_min, raise_max = self.get_bet_limits(player)
        options = [Bet.FOLD]
        params = dict()
        if call_delta==0:
            options.append(Bet.CHECK)
        elif call_delta>0 and call_delta<raise_max:
            options.append(Bet.CALL)
            params.update(call=call_delta)
        if raise_min<raise_max:
            options.append(Bet.RAISE)
            params.update(raise_min = raise_min, raise_max = raise_max)
        if raise_max:
            options.append(Bet.ALLIN)
            params.update(raise_max=raise_max)
        return options, params
    
    async def player_move(self):
        player = self.current_player
        player.bet_type = None
        await self.broadcast_PLAYER_MOVE()
        try:
            self.bet_event.clear()
            self.log_info("wait (%ss) for player %s ...", self.wait_timeout, player.user_id)
            await asyncio.wait_for(self.wait_for_player_bet(), self.wait_timeout)
        except asyncio.exceptions.TimeoutError:
            self.log_info("player timeout: %s", player.user_id)
        if player.bet_type is None:
            player.bet_type = Bet.FOLD
            player.bet_delta = 0
        await self.broadcast_PLAYER_BET()

    async def wait_for_player_bet(self):
        await self.bet_event.wait()

    def handle_bet(self, user_id, bet, delta):
        self.log_info("handle_bet: %s %s %s", user_id, bet, delta)
        p = self.current_player
        assert p.user_id == user_id
        assert Bet.verify(bet)

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
            assert raise_min<=delta and delta<=raise_max
            p.bet_delta = delta
        elif bet == Bet.ALLIN:
            p.bet_delta = p.balance
        else:
            raise ValueError('inalid bet type')

        p.bet_type = bet
        p.bet_amount += p.bet_delta
        p.user.balance -= p.bet_delta

        if self.bet_level<p.bet_amount:
            self.bet_id = p.user_id

        self.log_debug("player %s: balance: %s -> %s -> %s,  bet_id: %s", p.user_id, p.balance, p.bet_delta, p.bet_amount, self.bet_id)
        self.bet_event.set()

    async def round_begin(self, round):
        self.log_info("-> %s (%s)", round, self.round)
        self.round = round
        
        p = self.rotate_players(Player.ROLE_SMALL_BLIND)

        if self.round == Round.PREFLOP:
            if len(self.players)==2:
                p = self.rotate_players()
            for p in self.players:
                p.cards = []
                p.cards.append(self.deck.pop())
            for p in self.players:
                p.cards.append(self.deck.pop())
            for p in self.players:
                await self.broadcast_PLAYER_CARDS(p)
            
            p = self.rotate_players(Player.ROLE_SMALL_BLIND)
            p = self.players[0]

            # small blind
            assert p.role == Player.ROLE_SMALL_BLIND
            p.bet_type = Bet.SMALL_BLIND
            p.bet_delta = 1
            p.bet_amount += p.bet_delta
            p.user.balance -= p.bet_delta
            await self.broadcast_PLAYER_BET()
            p = self.rotate_players()

            # big blind
            assert p.role == Player.ROLE_BIG_BLIND
            p.bet_type = Bet.BIG_BLIND
            p.bet_delta = 2
            p.bet_amount += p.bet_delta
            p.user.balance -= p.bet_delta
            await self.broadcast_PLAYER_BET()
            p = self.rotate_players()
        
        elif len(self.players)==2:
            p = self.rotate_players()
        
        if self.round == Round.FLOP:
            self.deck.pop()
            for _ in range(3):
                self.cards.append(self.deck.pop())
            await self.broadcast_GAME_CARDS()

        elif self.round in (Round.TERN, Round.RIVER):
            self.cards.append(self.deck.pop())
            await self.broadcast_GAME_CARDS()

        self.bet_id = p.user_id
        
        # round begin sleep
        await asyncio.sleep(self.SLEEP_ROUND_BEGIN)
            

    async def round_end(self):
        if self.count_in_the_game>1 and self.count_has_options<=1:
            self.rotate_players(Player.ROLE_SMALL_BLIND)
            for p in self.players:
                if p.in_the_game and not p.cards_open:
                    p.cards_open = True
                    await self.broadcast_PLAYER_CARDS(p)
                    self.log_info("player %s: open cards %s", p.user_id, p.cards)

        players = [p for p in self.players if p.bet_amount>0]
        players.sort(key=lambda x: x.bet_amount)

        level = 0
        bank_delta = 0
        for p in players:
            if p.bet_type == Bet.FOLD:
                bank_delta += p.bet_amount
                p.bet_amount = 0
                p.bet_delta = 0
                continue
            elif not level:
                level = p.bet_amount
            bank_delta += level
            p.user.balance += p.bet_amount-level
            p.bet_amount = 0
            p.bet_delta = 0
            if p.bet_type == Bet.FOLD:
                continue
            p.bet_type = None

        self.bank += bank_delta
        self.bet_level = 0
        self.bets_all_same = True
        self.log_info("<- %s delta: %s bank: %s", self.round, bank_delta, self.bank)
        event = GAME_ROUND(amount = self.bank, delta = bank_delta)
        await self.broadcast(event)

        # end round sleep
        await asyncio.sleep(self.SLEEP_ROUND_END)

    def rotate_players(self, role=None):
        while True:
            self.players.append(self.players.pop(0))
            if not role or role==self.current_player.role:
                break
        return self.players[0]
    
    async def on_end(self):
        while self.current_player.user_id != self.bet_id:
            self.rotate_players()

        winners = []
        best_hand = None
        for p in self.players:
            if not p.in_the_game:
                continue
            if len(self.cards)<5:
                winners.append(p)
                continue
            p.hand = get_player_best_hand(p.cards, self.cards)
            if best_hand:
                if p.hand.rank<best_hand.rank:
                    continue
                if p.hand.rank>best_hand.rank:
                    winners = []
            winners.append(p)
            best_hand = p.hand
            if not p.cards_open and self.count_in_the_game>1:
                p.cards_open = True
                await self.broadcast_PLAYER_CARDS(p)
                self.log_info("player %s: open cards %s -> %s, %s", p.user_id, p.cards, p.hand, p.hand.rank)
                await asyncio.sleep(self.SLEEP_SHOWDOWN_CARDS)

        balance_delta = self.bank
        p = winners[0]
        p.user.balance += balance_delta

        winners = []
        w = dict(
            user_id = p.user_id,
            balance = p.balance,
            delta = p.balance - p.balance_0
        )
        self.log_info("winner: %s", w)
        winners.append(w)
        event = GAME_END(winners=winners)
        await self.broadcast(event)
        await asyncio.sleep(self.SLEEP_GAME_END)


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
        
    async def broadcast_PLAYER_MOVE(self):
        player = self.current_player
        options, params = self.get_bet_options(player)
        event = GAME_PLAYER_MOVE(
            user_id = player.user_id,
            options = options, 
            **params
        )
        await self.broadcast(event)

