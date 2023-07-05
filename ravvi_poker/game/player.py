from typing import List, Tuple
from .user import User
from .bet import Bet

class Player:

    ROLE_DEFAULT = 0
    ROLE_DEALER = 1
    ROLE_SMALL_BLIND = 2
    ROLE_BIG_BLIND = 3

    def __init__(self, user: User) -> None:
        self.user = user
        self.role = Player.ROLE_DEFAULT
        self.cards = None
        self.cards_open = False
        self.hand = None
        self.active = True
        self.bet_type = None
        self.bet_amount = 0
        self.bet_delta = 0
        self.bet_total = 0
        self.balance_0 = user.balance

    @property
    def user_id(self) -> int:
        return self.user.id
   
    @property
    def balance(self) -> int:
        return self.user.balance
    
    @property
    def bet_max(self) -> int:
        return self.bet_amount + self.balance
        
    @property
    def in_the_game(self) -> bool:
        return self.bet_type!=Bet.FOLD
    
    @property
    def has_bet_opions(self) -> bool:
        return self.in_the_game and self.balance
    
    