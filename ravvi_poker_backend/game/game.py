import logging
import time
import random
import asyncio

from .event import Event, GAME_BEGIN, PLAYER_CARDS, GAME_CARDS, PLAYER_BET, GAME_PLAYER_MOVE, GAME_ROUND, GAME_END
from .user import User

class Player:

    ROLE_DEALER = "D"
    ROLE_SMALL_BLIND = "SB"
    ROLE_BIG_BLIND = "BB"
    ROLE_PLAYER = "P"

    def __init__(self, user: User) -> None:
        self.user = user
        self.role = None
        self.cards = None
        self.cards_open = False
        self.active = True
        self.bet_type = None
        self.bet_amount = 0
        self.bet_delta = 0

    @property
    def user_id(self) -> int:
        return self.user.user_id
   
    @property
    def user_balance(self) -> int:
        return self.user.balance
    
    @property
    def bet_max(self):
        return self.bet_amount + self.user_balance


class Game:

    logger = logging.getLogger(__name__)

    ROUND_PREFLOP = 0
    ROUND_FLOP = 1
    ROUND_TERN = 2
    ROUND_RIVER = 3
    ROUND_SHOWDOWN = 4

    BET_FOLD = 1
    BET_SMALL_BLIND = 11
    BET_BIG_BLIND = 12
    BET_CALL = 21
    BET_CHECK = 22
    BET_RAISE = 30
    BET_ALLIN = 99

    def __init__(self, users, *, deck=None) -> None:
        self.table = None
        self.game_id = None
        self.players = [Player(u) for u in users]
        self.dealer_id = self.players[0].user_id
        self.bank = 0
        self.active_count = 0
        self.bet_level = 0
        self.bets_all_same = False
        self.wait_timeout = 60
        if deck:
            self.deck = reversed(deck)
        else:
            self.deck = list(range(1,53))
            random.shuffle(self.deck)
        self.cards = None

    @classmethod
    def rounds(cls):
        if not hasattr(cls, '_rounds'):
            cls._rounds = {v:k[6:] for k, v in cls.__dict__.items() if k[:6]=='ROUND_'}
        return cls._rounds

    @classmethod
    def round_name(cls, code: int):
        return cls.rounds().get(code)

    @classmethod
    def bets(cls):
        if not hasattr(cls, '_bets'):
            cls._bets = {v:k[4:] for k, v in cls.__dict__.items() if k[:4]=='BET_'}
        return cls._bets

    @classmethod
    def bet_name(cls, code: int):
        return cls.bets().get(code)

    @classmethod
    def bet_code(cls, name: str):
        return getattr(cls, f'BET_{name}', -1)
    
    @property
    def current_player(self):
        return self.players[0]
    
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
        player = self.players[0]
        event = PLAYER_BET(
            user_id = player.user_id,
            bet = player.bet_type,
            delta = player.bet_delta,
            amount = player.bet_amount,
            balance = player.user_balance
        )
        await self.broadcast(event)
        
    async def broadcast_PLAYER_MOVE(self):
        player = self.players[0]
        options = [self.BET_FOLD]
        min_delta = self.bet_level-player.bet_amount
        min_raise, max_raise = self.bet_level*2, player.bet_max
        if min_delta==0:
            options.append(self.BET_CHECK)
        elif min_delta<player.user_balance:
            options.append(self.BET_CALL)
        if min_raise<max_raise:
            options.append(self.BET_RAISE)
        else:
            min_raise = None
        if player.user_balance>0:
            options.append(self.BET_ALLIN)

        event = GAME_PLAYER_MOVE(
            user_id = player.user_id,
            options = options
        )
        if min_raise:
            event.update(
                raise_min = min_raise, 
                raise_max = max_raise
            )
        await self.broadcast(event)

    async def sleep(self, timeout):
        player = self.current_player
        deadline = time.time() + timeout
        while time.time()<deadline:
            await asyncio.sleep(1)
            if player.bet_type:
                break

    async def wait_for_player(self):
        player = self.current_player
        player.bet_type = None
        await self.broadcast_PLAYER_MOVE()
        await self.sleep(self.wait_timeout)
        if player.bet_type in (self.BET_CALL, self.BET_CHECK):
            player.bet_delta = self.bet_level-player.bet_amount
            player.bet_amount += player.bet_delta
            player.user.balance -= player.bet_delta
        elif player.bet_type == self.BET_RAISE:
            pass
        elif player.bet_type == self.BET_ALLIN:
            player.bet_delta = player.user.balance
            player.bet_amount += player.bet_delta
            player.user.balance -= player.bet_delta
        else:
            player.bet_type = self.BET_FOLD
            
        await self.broadcast_PLAYER_BET()

    def update_round_stat(self):
        # filter active players
        players = [p for p in self.players if p.bet_type!=self.BET_FOLD]
        self.active_count = len(players)
        self.bet_level = 0
        self.bets_all_same = True
        if self.active_count<1:
            return
        self.bet_level = players[0].bet_amount
        for p in players[1:]:
            if p.bet_amount==self.bet_level:
                continue
            if self.bet_level==p.bet_amount:
                continue
            self.bet_level = max(self.bet_level, p.bet_amount)
            self.bets_all_same = False
        print(f"status: active_count:{self.active_count} bet_level:{self.bet_level} all_same:{self.bets_all_same}")

    async def round_end(self, next_round):
        self.logger.info("<- %s", self.round_name(self.round))
        
        bank_delta = 0
        for p in self.players:
            bank_delta += p.bet_amount
            p.bet_amount = 0
            p.bet_delta = 0
            if p.bet_type != self.BET_FOLD:
                p.bet_type = None
        self.bank += bank_delta

        event = GAME_ROUND(amount = self.bank, delta = bank_delta)
        await self.broadcast(event)
        if not next_round:
            return

        self.round = next_round
        if self.round == self.ROUND_FLOP:
            for _ in range(3):
                self.cards.append(self.deck.pop())
            await self.broadcast_GAME_CARDS()
        elif self.round in (self.ROUND_TERN, self.ROUND_RIVER):
            self.cards.append(self.deck.pop())
            await self.broadcast_GAME_CARDS()
                       
        self.logger.info("-> %s", self.round_name(self.round))

    async def on_begin(self):
        self.players[0].role = Player.ROLE_DEALER
        self.players[1].role = Player.ROLE_SMALL_BLIND
        self.players[2].role = Player.ROLE_BIG_BLIND
        self.round = self.ROUND_PREFLOP
        await self.broadcast_GAME_BEGIN()
        for p in self.players:
            self.logger.info('%s: balance=%s', p.user_id, p.user_balance)

        self.cards = []
        for p in self.players:
            p.cards = []
            for _ in range(2):
                p.cards.append(self.deck.pop())
        for p in self.players:
            await self.broadcast_PLAYER_CARDS(p)
            
        p = self.rotate()
        p.bet_type = self.BET_SMALL_BLIND
        p.bet_delta = 1
        p.bet_amount += p.bet_delta
        p.user.balance -= p.bet_delta
        await self.broadcast_PLAYER_BET()

        p = self.rotate()
        p.bet_type = self.BET_BIG_BLIND
        p.bet_delta = 2
        p.bet_amount += p.bet_delta
        p.user.balance -= p.bet_delta
        await self.broadcast_PLAYER_BET()

        self.update_round_stat()
        
        self.rotate()

    async def run_step(self):
        player = self.current_player

        if player.bet_type not in [self.BET_FOLD, self.BET_ALLIN]:
            await self.wait_for_player()
            
        self.update_round_stat()
        if self.active_count<2:
            await self.round_end(None)
            return False

        if self.round == self.ROUND_PREFLOP and player.role==Player.ROLE_BIG_BLIND and self.bets_all_same:
            await self.round_end(self.ROUND_FLOP)
            self.rotate(forward=False)
        elif self.round in (self.ROUND_FLOP, self.ROUND_TERN, self.ROUND_RIVER) and player.role==Player.ROLE_DEALER and self.bets_all_same:
            await self.round_end(self.round+1)
            self.rotate(forward=True)
        else:
            self.rotate(forward=True)

        return self.round != self.ROUND_SHOWDOWN

    async def on_end(self):
        players = [p for p in self.players if p.bet_type!=self.BET_FOLD]
        winners = []
        if len(players):
            p = players[0]
            balance_delta = self.bank
            p.user.balance += balance_delta
            w = dict(
                user_id = p.user_id,
                balance = p.user_balance,
                delta = balance_delta
            )
            winners.append(w)
        event = GAME_END(winners=winners)
        await self.broadcast(event)

    async def run(self):
        self.logger.info("begin")
        await self.on_begin()
        while await self.run_step():
            pass
        await self.on_end()
        self.logger.info("end")


    def rotate(self, forward=True):
        if forward:
            self.players.append(self.players.pop(0))
        else:
            self.players.insert(0, self.players.pop(-1))
        return self.players[0]
    
