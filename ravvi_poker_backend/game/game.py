class Player:

    ROLE_DEALER = "D"
    ROLE_SMALL_BLIND = "SB"
    ROLE_BIG_BLIND = "BB"
    ROLE_PLAYER = "P"

    def __init__(self, user) -> None:
        self.user = user
        self.cards = None
        self.role = None
        self.bet_last = None
        self.bet_amount = 0

    @property
    def user_id(self):
        return self.user.user_id
   
    def __str__(self) -> str:
        return f"Player({self.user_id}, {self.role} {self.bet_last} {self.bet_amount})"
    
    def __repr__(self) -> str:
        return f"Player({self.user_id}, {self.role} {self.bet_last} {self.bet_amount})"

class Game:

    ROUND_PREFLOP = 0
    ROUND_FLOP = 1
    ROUND_TERN = 2
    ROUND_RIVER = 3
    ROUND_SHOWDOWN = 4

    def __init__(self, users) -> None:
        self.players = [Player(u) for u in self.users]
        self.players[0].role = Player.ROLE_DEALER
        self.players[1].role = Player.ROLE_SMALL_BLIND
        self.players[2].role = Player.ROLE_BIG_BLIND
        self.round = None

    @classmethod
    def rounds(cls):
        if not hasattr(cls, '_rounds'):
            cls._rounds = [(k,v) for k, v in cls.__dict__.items() if k[:6]=='ROUND_']
            cls._rounds.sort(key=lambda x: x[1])
        return cls._rounds

    @classmethod
    def round_name(cls, idx):
        return cls.rounds()[idx][0]
        

    @property
    def current_player(self):
        return self.players[0]

    def rotate(self, forward=True):
        if forward:
            self.players.append(self.players.pop(0))
        else:
            self.players.insert(0, self.players.pop(-1))
        return self.players[0]
    
    def print_state(self):
        print("   = ", self.players)

    def begin(self):
        p = self.players[0]
        self.broadcast( type='GAME_INFO', players = [x.user_id for x in self.users], dealer_id = p.user_id)
        
        self.round = self.ROUND_PREFLOP
        print(" --> ", self.round_name(self.round))

        p = self.rotate()
        #self.print_state()
        self.onPlayerBet(None, "SB", 1)
        self.onPlayerBet(None, "BB", 2)

    def onPlayerBet(self, user_id, bet, amount):
        p = self.players[0]
        if user_id and p.user_id != user_id:
            return False
        max_bet = max(p.bet_amount for p in self.players)
        if bet in ('SB','BB'):
            p.bet_last, p.bet_amount = bet, amount
        elif bet=='CALL':
            p.bet_last, p.bet_amount = bet, max_bet
        
        self.broadcast(type='PLAYER_BET', user_id = p.user_id, bet = p.bet_last, amount = p.bet_amount)
        all_same = all(p.bet_amount==max_bet for p in self.players)
        if self.round == self.ROUND_PREFLOP:
            if p.role==Player.ROLE_BIG_BLIND and all_same:
                print(" <-- ", self.round_name(self.round))
                self.round = self.ROUND_FLOP
                print(" --> ", self.round_name(self.round))
                p = self.rotate(forward=False)
            else:
                p = self.rotate()
        elif self.round in (self.ROUND_FLOP, self.ROUND_TERN, self.ROUND_RIVER):
            if p.role==Player.ROLE_DEALER and all_same:
                print(" <-- ", self.round_name(self.round))
                self.round += 1
                print(" --> ", self.round_name(self.round))
            p = self.rotate()
        self.print_state()
        self.broadcast(type='GAME_PLAYER_MOVE', user_id = p.user_id)
        return True
        
        
    def broadcast(self, **kwargs):
        print(kwargs)

