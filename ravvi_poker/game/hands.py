from itertools import combinations
from enum import Enum, IntEnum, unique

from .cards import Card

@unique
class HandType(Enum):
    HIGH_CARD = "CH"
    ONE_PAIR = "P1"
    TWO_PAIRS = "P2"
    THREE_OF_KIND = "C3"
    FOUR_OF_KIND = "C4"
    FULL_HOUSE = "HS"
    STRAIGHT = "ST"
    FLUSH = "FL"
    STRAIGHT_FLUSH = "FS"
    ROYAL_FLUSH = "FR"

    @classmethod
    def decode(cls, x):
        if isinstance(x, HandType):
            return x
        elif isinstance(x, str):
            r = cls.__members__.get(x, None)
            if r is not None:
                return r
        return cls._value2member_map_[x]

class Hand:
    def __init__(self, cards, deck36=False) -> None:
        self.cards = [x if isinstance(x, Card) else Card(x) for x in cards]
        self.cards.sort(key=lambda x: (-x.rank, x.suit))
        self.mask = 0
        for c in self.cards:
            self.mask |= c.mask
        self.type = self.get_type(deck36) if self.cards else None
        self.rank = None
        self.value = 0

    def __str__(self) -> str:
        s = " ".join([str(c) for c in self.cards])
        return s

    def get_type(self, deck36=False):
        flush = self.check_flush()
        straight = self.check_straight(deck36)
        if flush and straight:
            return HandType.STRAIGHT_FLUSH, straight[1]
        elif flush:
            return flush
        elif straight:
            return straight
        return self.check_same_rank()

    def check_flush(self):
        if len(self.cards)<5:
            return None
        for suit_index in range(4):
            suit_index *= 13
            suit_mask = (self.mask >> suit_index) & 0b1111111111111
            match = bin(suit_mask)[2:]
            cards_rank = [i for i, b in enumerate(reversed(match), 2) if b == "1"]
            if len(cards_rank) == 5:
                return HandType.FLUSH, *reversed(cards_rank)
        return None

    def check_straight(self, deck36):
        if len(self.cards)<5:
            return None
        if deck36:
            straight_idx0 = 9
            straight_masks = [
                0b1000011110000,  # 09
                0b0000111110000,  # 10
                0b0001111100000,  # 11
                0b0011111000000,  # 12
                0b0111110000000,  # 13
                0b1111100000000,  # 14
            ]
            
        else:
            straight_idx0 = 5
            straight_masks = [
                0b1000000001111,  # 05
                0b0000000011111,  # 06
                0b0000000111110,  # 07
                0b0000001111100,  # 08
                0b0000011111000,  # 09
                0b0000111110000,  # 10
                0b0001111100000,  # 11
                0b0011111000000,  # 12
                0b0111110000000,  # 13
                0b1111100000000,  # 14
            ]
        rank_mask = 0
        for suit_index in range(4):
            suit_index *= 13
            suit_mask = (self.mask >> suit_index) & 0b1111111111111
            rank_mask |= suit_mask
        for i, mask in enumerate(straight_masks, straight_idx0):
            if rank_mask & mask == mask:
                return HandType.STRAIGHT, i
        return None

    def check_same_rank(self):
        result = []
        mask = 0
        for _ in range(4):
            mask = mask << 13
            mask |= 1
        for rank_idx in range(0, 13):
            rank_mask = mask << rank_idx
            match = self.mask & rank_mask
            counter = bin(match)[2:].count("1")
            if counter > 1:
                result.append((counter, rank_idx + 2))
        other_ranks = [c.rank for c in self.cards]
        for _, rank in result:
            other_ranks = [r for r in other_ranks if r != rank]
        other_ranks.sort(reverse=True)
        if len(result) == 1:
            counter, rank = result[0]
            if counter == 4:
                return HandType.FOUR_OF_KIND, rank, *other_ranks
            elif counter == 3:
                return HandType.THREE_OF_KIND, rank, *other_ranks
            elif counter == 2:
                return HandType.ONE_PAIR, rank, *other_ranks
            else:
                raise ValueError("error")
        elif len(result) == 2:
            result.sort(reverse=True)
            c1, r1 = result[0]
            c2, r2 = result[1]
            if c1 == 3 and c2 == 2:
                return HandType.FULL_HOUSE, r1, r2, *other_ranks
            elif c1 == 2 and c2 == 2:
                return HandType.TWO_PAIRS, r1, r2, *other_ranks
            else:
                raise ValueError("error")
        return HandType.HIGH_CARD, *other_ranks
