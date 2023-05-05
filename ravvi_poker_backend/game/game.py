import time
import random

class Player:

    ROLE_DEALER = "D"
    ROLE_SMALL_BLIND = "SB"
    ROLE_BIG_BLIND = "BB"
    ROLE_PLAYER = "P"

    def __init__(self, user) -> None:
        self.user = user
        self.cards = None
        self.role = None
        self.bet_type = None
        self.bet_amount = 0

    @property
    def user_id(self):
        return self.user.user_id
   
    def __str__(self) -> str:
        return f"Player({self.user_id}, {self.role} {self.bet_type} {self.bet_amount})"
    
    def __repr__(self) -> str:
        return f"Player({self.user_id}, {self.role} {self.bet_type} {self.bet_amount})"

class Game:

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
        self.players = [Player(u) for u in users]
        self.active_count = 0
        self.bet_level = 0
        self.bets_all_same = False
        self.wait_timeout = 5
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
    
    def broadcast(self, **kwargs):
        def smap(k, v):
            if k=='bet':
                name = self.bet_name(v)
                v = f"{name}({v})"
            return f"{k}: {v}"
        msg = ', '.join([smap(k,v) for k, v in kwargs.items()])
        print(msg)

    def broadcast_GAME_INFO(self):
        dealer = self.players[0]
        self.broadcast(type='GAME_INFO', 
                       players = [x.user_id for x in self.players], 
                       dealer_id = dealer.user_id,
                       round = self.round
                       )

    def broadcast_PLAYER_CARDS(self, player, open=False):
        self.broadcast(type='PLAYER_CARDS', 
                       user_id = player.user_id,
                       cards = player.cards,
                       open = open
                       )

    def broadcast_GAME_CARDS(self):
        self.broadcast(type='GAME_CARDS', 
                       cards = self.cards
                       )
       
    def broadcast_PLAYER_BET(self):
        player = self.players[0]
        self.broadcast(type='PLAYER_BET', 
                       user_id = player.user_id, 
                       bet = player.bet_type, 
                       amount = player.bet_amount
                       )
        
    def broadcast_PLAYER_MOVE(self):
        player = self.players[0]
        self.broadcast(type='PLAYER_MOVE', user_id = player.user_id)


    def on_begin(self):
        self.players[0].role = Player.ROLE_DEALER
        self.players[1].role = Player.ROLE_SMALL_BLIND
        self.players[2].role = Player.ROLE_BIG_BLIND
        self.round = self.ROUND_PREFLOP
        self.broadcast_GAME_INFO()

        self.cards = []
        for p in self.players:
            p.cards = []
            for _ in range(2):
                p.cards.append(self.deck.pop())
        for p in self.players:
            self.broadcast_PLAYER_CARDS(p, open=False)
            
        
        p = self.rotate()
        p.bet_type = self.BET_SMALL_BLIND
        p.bet_amount = 1
        self.broadcast_PLAYER_BET()

        p = self.rotate()
        p.bet_type = self.BET_BIG_BLIND
        p.bet_amount = 2
        self.broadcast_PLAYER_BET()

        self.update_round_stat()
        
        p = self.rotate()

    def on_end(self):
        #TODO
        pass

    def sleep(self, timeout):
        player = self.current_player
        deadline = time.time() + timeout
        while time.time()<deadline:
            time.sleep(1)
            if player.bet_type:
                break

    def wait_for_player(self, timeout=5):
        player = self.current_player
        player.bet_type = None
        self.broadcast_PLAYER_MOVE()
        self.sleep(self.wait_timeout)
        if player.bet_type is None:
            player.bet_type = self.BET_FOLD
        elif player.bet_type in (self.BET_CALL, self.BET_CHECK):
            player.bet_amount = self.bet_level
        elif player.bet_amount is None:
            player.bet_amount = self.bet_level
            
        self.broadcast_PLAYER_BET()

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
            if isinstance(p.bet_amount, int):
                if self.bet_level==p.bet_amount:
                    continue
                self.bet_level = max(self.bet_level, p.bet_amount)
            self.bets_all_same = False
        print(f" -> ({self.active_count}) {self.bet_level} {self.bets_all_same}")

    def run_step(self):
        player = self.current_player
        print(player)

        if player.bet_type!=self.BET_FOLD:
            self.wait_for_player()
            
        self.update_round_stat()
        if self.active_count<2:
            return False

        if self.round == self.ROUND_PREFLOP and player.role==Player.ROLE_BIG_BLIND and self.bets_all_same:
            print(" <-- ", self.round_name(self.round))
            self.round = self.ROUND_FLOP
            print(" --> ", self.round_name(self.round))

            for _ in range(3):
                self.cards.append(self.deck.pop())
            self.broadcast_GAME_CARDS()

            self.rotate(forward=False)

        elif self.round in (self.ROUND_FLOP, self.ROUND_TERN, self.ROUND_RIVER) and player.role==Player.ROLE_DEALER and self.bets_all_same:
            print(" <-- ", self.round_name(self.round))
            self.round += 1
            print(" --> ", self.round_name(self.round))
            
            if self.round in (self.ROUND_TERN, self.ROUND_RIVER):
                self.cards.append(self.deck.pop())
                self.broadcast_GAME_CARDS()

            self.rotate(forward=True)
        else:
            self.rotate(forward=True)

        return self.round != self.ROUND_SHOWDOWN


    def run(self):
        self.on_begin()

        while self.run_step():
            pass

        self.on_end()


    def rotate(self, forward=True):
        if forward:
            self.players.append(self.players.pop(0))
        else:
            self.players.insert(0, self.players.pop(-1))
        return self.players[0]
    
