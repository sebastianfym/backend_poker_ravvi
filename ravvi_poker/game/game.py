from typing import List
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
    SHOWDOWN = 5


class Game(ObjectLogger):

    def __init__(self, table, game_id, users: List[User], *, deck=None) -> None:
        super().__init__(__name__+f".{game_id}")
        self.table = table
        self.game_id = game_id
        self.round = None
        self.players = [Player(u) for u in users]
        self.dealer_id = self.players[0].user_id
        self.active_count = 0
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

    @property
    def current_player(self):
        return self.players[0]
    
    async def run(self):
        self.log_info("begin")
        await self.on_begin()
        while await self.run_step():
            pass
        await self.on_end()
        self.log_info("end")

    async def on_begin(self):
        assert self.round is None
        # init 
        self.round = Round.PREFLOP
        await self.broadcast_GAME_BEGIN()

        # cards
        self.cards = []
        for p in self.players:
            p.cards = []
            for _ in range(2):
                p.cards.append(self.deck.pop())
        for p in self.players:
            await self.broadcast_PLAYER_CARDS(p)
            
        # assign playes roles
        # dealer
        p = self.players[0]
        p.role = Player.ROLE_DEALER

        # small blind
        p = self.rotate_players()
        p.role = Player.ROLE_SMALL_BLIND
        p.bet_type = Bet.SMALL_BLIND
        p.bet_delta = 1
        p.bet_amount += p.bet_delta
        p.user.balance -= p.bet_delta
        await self.broadcast_PLAYER_BET()

        # big blind
        p = self.rotate_players()
        p.role = Player.ROLE_BIG_BLIND
        p.bet_type = Bet.BIG_BLIND
        p.bet_delta = 2
        p.bet_amount += p.bet_delta
        p.user.balance -= p.bet_delta
        await self.broadcast_PLAYER_BET()

        self.rotate_players()
        self.update_status()        

    async def run_step(self):
        player = self.current_player

        if player.has_bet_opions:
            await self.player_move()
            self.update_status()
        
        if self.active_count<2:
            await self.round_end(None)
            return False

        if self.round == Round.PREFLOP and player.role==Player.ROLE_BIG_BLIND and self.bets_all_same:
            await self.round_end(Round.FLOP)
            self.rotate_players(forward=False)
        elif self.round in (Round.FLOP, Round.TERN, Round.RIVER) and player.role==Player.ROLE_DEALER and self.bets_all_same:
            await self.round_end(self.round+1)
            self.rotate_players(forward=True)
        else:
            self.rotate_players(forward=True)

        return self.round != Round.SHOWDOWN
    
    
    def update_status(self):
        # filter players with bet options
        players = [p for p in self.players if p.has_bet_opions]        
        self.active_count = len(players)
        self.bet_level = 0
        self.bets_all_same = True
        if not self.active_count:
            return
        self.bet_level = players[0].bet_amount
        for p in players[1:]:
            if p.bet_amount==self.bet_level:
                continue
            self.bet_level = max(self.bet_level, p.bet_amount)
            self.bets_all_same = False
        self.log_info(f"status: active_count:{self.active_count} bet_level:{self.bet_level} all_same:{self.bets_all_same}")
    
    async def player_move(self):
        player = self.current_player
        player.bet_type = None
        await self.broadcast_PLAYER_MOVE()
        await self.wait_for_player()
        if player.bet_type is None:
            player.bet_type = Bet.FOLD
        await self.broadcast_PLAYER_BET()

    async def wait_for_player(self):
        player = self.current_player
        deadline = time.time() + self.wait_timeout
        while time.time()<deadline:
            await asyncio.sleep(1)
            if player.bet_type:
                break

    def handle_bet(self, user_id, bet, amount):
        self.log_info("handle_bet: %s %s %s", user_id, bet, amount)
        p = self.current_player
        assert p.user_id == user_id
        assert Bet.verify(bet)
        raise_min = self.bet_level*2
        raise_max = p.bet_max

        if bet == Bet.FOLD:
            p.bet_delta = 0
        elif bet == Bet.CHECK:
            if p.bet_amount!=self.bet_level:
                raise ValueError(f"player {p.user_id}: bet {p.bet_amount} != current_level {self.bet_level}")
            p.bet_delta = 0
        elif bet == Bet.CALL:
            assert p.bet_amount<self.bet_level
            p.bet_delta = self.bet_level-p.bet_amount
        elif bet == Bet.RAISE:
            assert raise_min<=amount and amount<=raise_max
            p.bet_delta = amount-p.bet_amount
        elif bet == Bet.ALLIN:
            p.bet_delta = p.balance
        else:
            raise ValueError('inalid bet type')

        p.bet_type = bet
        p.bet_amount += p.bet_delta
        p.user.balance -= p.bet_delta
        self.log_debug("player %s: balance: %s -> %s -> %s", p.user_id, p.balance, p.bet_delta, p.bet_amount)

    async def round_end(self, next_round):
        self.log_info("<- %s", self.round)
        bank_delta = 0
        for p in self.players:
            bank_delta += p.bet_amount
            p.bet_amount = 0
            p.bet_delta = 0
            if p.bet_type != Bet.FOLD:
                p.bet_type = None
        self.bank += bank_delta
        self.bet_level = 0
        self.bets_all_same = True
        event = GAME_ROUND(amount = self.bank, delta = bank_delta)
        await self.broadcast(event)
        if not next_round:
            return
        self.round = next_round
        if self.round == Round.FLOP:
            for _ in range(3):
                self.cards.append(self.deck.pop())
            await self.broadcast_GAME_CARDS()
        elif self.round in (Round.TERN, Round.RIVER):
            self.cards.append(self.deck.pop())
            await self.broadcast_GAME_CARDS()
        self.log_info("-> %s bank: %s", self.round, self.bank)

    def rotate_players(self, forward=True):
        if forward:
            self.players.append(self.players.pop(0))
        else:
            self.players.insert(0, self.players.pop(-1))
        return self.players[0]
    
    async def on_end(self):
        while self.current_player.role != Player.ROLE_SMALL_BLIND:
            self.rotate_players()
        players = [p for p in self.players if p.bet_type != Bet.FOLD]
        winners = []
        if len(players)>1:
            for i, p in enumerate(players):
                if i!=0:
                    await asyncio.sleep(1)
                p.cards_open = True
                p.hand = get_player_best_hand(p.cards, self.cards)
                await self.broadcast_PLAYER_CARDS(p)
                self.log_info("player %s: open cards %s -> %s, %s", p.user_id, p.cards, p.hand, p.hand.rank)
            players.sort(reverse=True, key=lambda x: x.hand.rank)
            for i, p in enumerate(players):
                self.log_info("%s: %s: open cards %s -> %s, %s", i+1, p.user_id, p.cards, p.hand, p.hand.rank)
        
        p = players[0]
        winners.append(p)

        balance_delta = self.bank
        p = winners[0]
        p.user.balance += balance_delta

        winners = []
        w = dict(
            user_id = p.user_id,
            balance = p.balance,
            delta = balance_delta
        )
        self.log_info("winner: %s", w)
        winners.append(w)
        event = GAME_END(winners=winners)
        await self.broadcast(event)

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
        options, params = player.get_bet_options(self.bet_level)
        event = GAME_PLAYER_MOVE(
            user_id = player.user_id,
            options = options, 
            **params
        )
        await self.broadcast(event)

