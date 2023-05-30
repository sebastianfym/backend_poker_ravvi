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

#logging.basicConfig(level=logging.DEBUG)

class Game(ObjectLogger):

    def __init__(self, table, game_id, users: List[User], *, deck=None) -> None:
        super().__init__(__name__+f".{game_id}")
        self.table = table
        self.game_id = game_id
        self.round = None
        self.players = [Player(u) for u in users]
        self.dealer_id = self.players[0].user_id
        self.count_in_the_game = 0
        self.count_has_options = 0
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
        self.players[0].role = Player.ROLE_DEALER
        self.players[1].role = Player.ROLE_SMALL_BLIND
        self.players[2].role = Player.ROLE_BIG_BLIND

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

        #if not self.count_has_options:
        #    # open cards
        #    pass

        if self.round == Round.PREFLOP:
            if player.role==Player.ROLE_BIG_BLIND and self.bets_all_same:
                await self.round_end()
                await self.round_begin(Round.FLOP)
                return True
        elif self.round == Round.FLOP:
            if  player.role==Player.ROLE_DEALER and self.bets_all_same:
                await self.round_end()
                await self.round_begin(Round.TERN)
                return True
        elif self.round == Round.TERN and player.role==Player.ROLE_DEALER:
            if self.bets_all_same:
                await self.round_end()
                await self.round_begin(Round.RIVER)
                return True
        elif self.round == Round.RIVER and player.role==Player.ROLE_DEALER:
            if self.bets_all_same:
                await self.round_end()
                await self.round_begin(Round.SHOWDOWN)
                return False

        self.rotate_players()
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
        self.log_info(f"status: in_the_game:{self.count_in_the_game} has_options:{self.count_has_options} bet_level:{self.bet_level} bets_all_same:{self.bets_all_same}")
    
    async def player_move(self):
        player = self.current_player
        player.bet_type = None
        await self.broadcast_PLAYER_MOVE()
        try:
            self.bet_event.clear()
            self.log_info("wait for player %s ...", player.user_id)
            await asyncio.wait_for(self.wait_for_player_bet(), self.wait_timeout)
        except TimeoutError:
            self.log_info("player timeout: %s", player.user_id)
        if player.bet_type is None:
            player.bet_type = Bet.FOLD
        await self.broadcast_PLAYER_BET()

    async def wait_for_player_bet(self):
        await self.bet_event.wait()

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
        self.bet_event.set()

    async def round_begin(self, round):
        self.log_info("-> %s (%s)", round, self.round)
        self.round = round
        
        p = self.rotate_players(Player.ROLE_SMALL_BLIND)

        if self.round == Round.PREFLOP:
            while True:
                p.cards = []
                for _ in range(2):
                    p.cards.append(self.deck.pop())
                await self.broadcast_PLAYER_CARDS(p)
                p = self.rotate_players()
                if p.role ==Player.ROLE_SMALL_BLIND:
                    break

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

        elif not self.count_has_options:
            while True:
                if p.in_the_game and not p.cards_open:
                    p.cards_open = True
                    await self.broadcast_PLAYER_CARDS(p)
                    self.log_info("player %s: open cards %s", p.user_id, p.cards)
                p = self.rotate_players()
                if p.role ==Player.ROLE_SMALL_BLIND:
                    break
        
        if self.round == Round.FLOP:
            for _ in range(3):
                self.cards.append(self.deck.pop())
            await self.broadcast_GAME_CARDS()
        elif self.round in (Round.TERN, Round.RIVER):
            self.cards.append(self.deck.pop())
            await self.broadcast_GAME_CARDS()

    async def round_end(self):
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
        self.log_info("<- %s bank: %s", self.round, self.bank)
        event = GAME_ROUND(amount = self.bank, delta = bank_delta)
        await self.broadcast(event)

    def rotate_players(self, role=None):
        while True:
            self.players.append(self.players.pop(0))
            if not role or role==self.current_player.role:
                break
        return self.players[0]
    
    async def on_end(self):
        self.rotate_players(Player.ROLE_SMALL_BLIND)

        players = [p for p in self.players if p.in_the_game]
        winners = []
        if len(players)>1:
            for i, p in enumerate(players):
                p.hand = get_player_best_hand(p.cards, self.cards)
                if not p.cards_open:
                    if i!=0:
                        await asyncio.sleep(1)
                    p.cards_open = True
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
            delta = p.balance - p.balance_0
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

