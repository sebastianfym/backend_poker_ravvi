from enum import Enum, unique

from ..cards import Card


@unique
class HandType(Enum):
    HIGH_CARD = "H"
    ONE_PAIR = "P1"
    TWO_PAIRS = "P2"
    THREE_OF_KIND = "K3"
    FOUR_OF_KIND = "K4"
    FULL_HOUSE = "FH"
    STRAIGHT = "S"
    FLUSH = "F"
    STRAIGHT_FLUSH = "SF"
    ROYAL_FLUSH = "RF"

    @classmethod
    def decode(cls, x):
        if isinstance(x, HandType):
            return x
        r = cls.__members__.get(x, None)
        if r is not None:
            return r
        return cls._value2member_map_[x]

    def __str__(self) -> str:
        return super().__str__()


low_hands_hashes = {
    # low 5
    hash((5, 4, 3, 2, 14)): {"num": 0},

    # low 6
    hash((6, 4, 3, 2, 14)): {"num": 1},

    hash((6, 5, 3, 2, 14)): {"num": 2},
    hash((6, 5, 4, 2, 14)): {"num": 3},
    hash((6, 5, 4, 3, 14)): {"num": 4},
    hash((6, 5, 4, 3, 2)): {"num": 5},

    # low 7
    hash((7, 4, 3, 2, 14)): {"num": 6},

    hash((7, 5, 3, 2, 14)): {"num": 7},
    hash((7, 5, 4, 2, 14)): {"num": 8},
    hash((7, 5, 4, 3, 14)): {"num": 9},
    hash((7, 5, 4, 3, 2)): {"num": 10},

    hash((7, 6, 3, 2, 14)): {"num": 11},
    hash((7, 6, 4, 2, 14)): {"num": 12},
    hash((7, 6, 4, 3, 14)): {"num": 13},
    hash((7, 6, 4, 3, 2)): {"num": 14},
    hash((7, 6, 5, 2, 14)): {"num": 15},
    hash((7, 6, 5, 3, 14)): {"num": 16},
    hash((7, 6, 5, 3, 2)): {"num": 17},
    hash((7, 6, 5, 4, 14)): {"num": 18},
    hash((7, 6, 5, 4, 2)): {"num": 19},
    hash((7, 6, 5, 4, 3)): {"num": 20},

    # low 8
    hash((8, 4, 3, 2, 14)): {"num": 21},

    hash((8, 5, 3, 2, 14)): {"num": 22},
    hash((8, 5, 4, 2, 14)): {"num": 23},
    hash((8, 5, 4, 3, 14)): {"num": 24},
    hash((8, 5, 4, 3, 2)): {"num": 25},

    hash((8, 6, 3, 2, 14)): {"num": 26},
    hash((8, 6, 4, 2, 14)): {"num": 27},
    hash((8, 6, 4, 3, 14)): {"num": 28},
    hash((8, 6, 4, 3, 2)): {"num": 29},
    hash((8, 6, 5, 2, 14)): {"num": 30},
    hash((8, 6, 5, 3, 14)): {"num": 31},
    hash((8, 6, 5, 3, 2)): {"num": 32},
    hash((8, 6, 5, 4, 14)): {"num": 33},
    hash((8, 6, 5, 4, 2)): {"num": 34},
    hash((8, 6, 5, 4, 3)): {"num": 35},

    hash((8, 7, 3, 2, 14)): {"num": 36},
    hash((8, 7, 4, 2, 14)): {"num": 37},
    hash((8, 7, 4, 3, 14)): {"num": 38},
    hash((8, 7, 4, 3, 2)): {"num": 39},
    hash((8, 7, 5, 2, 14)): {"num": 40},
    hash((8, 7, 5, 3, 14)): {"num": 41},
    hash((8, 7, 5, 3, 2)): {"num": 42},
    hash((8, 7, 5, 4, 14)): {"num": 43},
    hash((8, 7, 5, 4, 2)): {"num": 44},
    hash((8, 7, 5, 4, 3)): {"num": 45},
    hash((8, 7, 6, 2, 14)): {"num": 46},
    hash((8, 7, 6, 3, 14)): {"num": 47},
    hash((8, 7, 6, 3, 2)): {"num": 48},
    hash((8, 7, 6, 4, 14)): {"num": 49},
    hash((8, 7, 6, 4, 2)): {"num": 50},
    hash((8, 7, 6, 4, 3)): {"num": 51},
    hash((8, 7, 6, 5, 14)): {"num": 52},
    hash((8, 7, 6, 5, 2)): {"num": 53},
    hash((8, 7, 6, 5, 3)): {"num": 54},
    hash((8, 7, 6, 5, 4)): {"num": 55},
}


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

    def get_low_type(self):
        # проверяем есть ли вообще смысл считать low_type
        if not len(card_ranks := [card_rank for card_rank in set([card.rank for card in self.cards])
                                  if card_rank <= 8 or card_rank == 14]) == 5:
            return None

        # получаем индекс силы
        card_ranks = sorted(card_ranks, reverse=True)
        if 14 in card_ranks:
            card_ranks = card_ranks[1:] + card_ranks[:1]
        card_ranks = tuple(card_ranks)

        return low_hands_hashes.get(card_ranks)

    def check_flush(self):
        if len(self.cards) < 5:
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
        if len(self.cards) < 5:
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
            return HandType.ONE_PAIR, rank, *other_ranks
        elif len(result) == 2:
            result.sort(reverse=True)
            c1, r1 = result[0]
            _, r2 = result[1]
            if c1 == 3:
                return HandType.FULL_HOUSE, r1, r2, *other_ranks
            return HandType.TWO_PAIRS, r1, r2, *other_ranks
        return HandType.HIGH_CARD, *other_ranks
