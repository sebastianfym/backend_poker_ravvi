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
    def has_bet_opions(self) -> bool:
        return self.bet_type!=Bet.FOLD and self.balance
    
    def get_bet_options(self, game_level) -> Tuple[List[Bet], dict]:
        raise_min = max(game_level*2, 2)
        raise_max = self.bet_max
        options = [Bet.FOLD]
        params = dict()
        if self.bet_amount==game_level:
            options.append(Bet.CHECK)
        elif game_level<raise_max:
            options.append(Bet.CALL)
            params.update(call=game_level)
        if raise_min<=raise_max:
            options.append(Bet.RAISE)
            params.update(raise_min = raise_min, raise_max = raise_max)
        if self.bet_amount<raise_max:
            options.append(Bet.ALLIN)
            params.update(raise_max=raise_max)
        return options, params
    