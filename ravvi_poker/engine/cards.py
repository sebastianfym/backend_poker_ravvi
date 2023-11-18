
class Card:
    RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]
    # (S)pades(♠) (C)lubs(♣) (D)iamonds(♦) (H)earts(♥)
    SUITS = ["♠", "♣", "♦", "♥"]
    SUITS2 = ["S", "C", "D", "H"]  

    def __init__(self, code=None, *, rank=None, suit=None) -> None:
        if code is None:
            code = self.encode(suit=suit, rank=rank)
        elif isinstance(code, str):
            code = self.parse(code)
        if code==0:
            self.code = 0
        elif code<1 or code>52:
            raise ValueError(f"invalid card code: {code}")
        else:
            self.code = code

    @classmethod
    def get_suite_idx(cls, suit):
        suit_idx = None
        if isinstance(suit, str):
            try:
                suit_idx = cls.SUITS.index(suit)
            except ValueError:
                try:
                    suit_idx = cls.SUITS2.index(suit)
                except ValueError:
                    pass
        elif isinstance(suit, int) and suit>=1 and suit<=4:
            suit_idx = suit-1
        if suit_idx is None:
            raise ValueError(f"invalid suit value: {suit}")
        return suit_idx
    
    @classmethod
    def get_rank_idx(cls, rank):
        rank_idx = None
        if isinstance(rank, str):
            try:
                rank_idx = cls.RANKS.index(rank)
            except ValueError:
                pass
        elif isinstance(rank, int) and rank>=2 and rank<=14:
            rank_idx = rank-2
        if rank_idx is None:
            raise ValueError(f"invalid rank value: {rank}")
        return rank_idx

    @classmethod
    def encode(cls, *, suit, rank) -> int:
        suit_idx = cls.get_suite_idx(suit)
        rank_idx = cls.get_rank_idx(rank)
        return suit_idx* 13 + rank_idx + 1
    
    @classmethod
    def parse(cls, x) -> int:
        if not isinstance(x, str) or len(x) != 2:
            raise ValueError("invalid card value {x}")
        return cls.encode(rank=x[0].upper(), suit=x[1].upper())

    @property
    def rank(self):
        if 1 <= self.code and self.code <= 52:
            return (self.code - 1) % 13 + 2
        else:
            return None

    @property
    def suit(self):
        if 1 <= self.code and self.code <= 52:
            return int((self.code - 1) / 13) + 1
        else:
            return None

    @property
    def mask(self):
        return 1 << self.code - 1 if self.code else 0

    def __str__(self) -> str:
        if self.code==0:
            return "XX"
        return f"{self.RANKS[self.rank-2]}{self.SUITS[self.suit-1]}"


def get_deck_52():
    return list(range(1, 53))


def get_deck_36():
    return list(filter(lambda x: Card(x).rank >= 6, get_deck_52()))


