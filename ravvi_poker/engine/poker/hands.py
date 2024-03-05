from enum import Enum, unique

from .board import Board
from ..cards import Card


@unique
class HandBelong(Enum):
    BOARD1 = "board1"
    BOARD2 = "board2"
    BOARD3 = "board3"
    LOW = "low"


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


@unique
class LowHandType(Enum):
    H_5432A = "5432A"

    H_6432A = "6432A"
    H_6532A = "6532A"
    H_6542A = "6542A"
    H_6543A = "6543A"
    H_65432 = "65432"

    H_7432A = "7432A"
    H_7532A = "7532A"
    H_7542A = "7542A"
    H_7543A = "7543A"
    H_75432 = "75432"
    H_7632A = "7632A"
    H_7642A = "7642A"
    H_7643A = "7643A"
    H_76432 = "76432"
    H_7652A = "7652A"
    H_7653A = "7653A"
    H_76532 = "76532"
    H_7654A = "7654A"
    H_76542 = "76542"
    H_76543 = "76543"

    H_8432A = "8432A"
    H_8532A = "8532A"
    H_8542A = "8542A"
    H_8543A = "8543A"
    H_85432 = "85432"
    H_8632A = "8632A"
    H_8642A = "8642A"
    H_8643A = "8643A"
    H_86432 = "86432"
    H_8652A = "8652A"
    H_8653A = "8653A"
    H_86532 = "86532"
    H_8654A = "8654A"
    H_86542 = "86542"
    H_86543 = "86543"
    H_8732A = "8732A"
    H_8742A = "8742A"
    H_8743A = "8743A"
    H_87432 = "87432"
    H_8752A = "8752A"
    H_8753A = "8753A"
    H_87532 = "87532"
    H_8754A = "8754A"
    H_87542 = "87542"
    H_87543 = "87543"
    H_8762A = "8762A"
    H_8763A = "8763A"
    H_87632 = "87632"
    H_8764A = "8764A"
    H_87642 = "87642"
    H_87643 = "87643"
    H_8765A = "8765A"
    H_87652 = "87652"
    H_87653 = "87653"
    H_87654 = "87654"

    @classmethod
    def decode(cls, x):
        if x is None:
            return None
        if isinstance(x, LowHandType):
            return x
        r = cls.__members__.get(x, None)
        if r is not None:
            return r
        return cls._value2member_map_[x]


low_hands_hashes = {
    # low 5
    hash((5, 4, 3, 2, 14)): LowHandType.H_5432A,

    # low 6
    hash((6, 4, 3, 2, 14)): LowHandType.H_6432A,

    hash((6, 5, 3, 2, 14)): LowHandType.H_6532A,
    hash((6, 5, 4, 2, 14)): LowHandType.H_6542A,
    hash((6, 5, 4, 3, 14)): LowHandType.H_6543A,
    hash((6, 5, 4, 3, 2)): LowHandType.H_65432,

    # low 7
    hash((7, 4, 3, 2, 14)): LowHandType.H_7432A,

    hash((7, 5, 3, 2, 14)): LowHandType.H_7532A,
    hash((7, 5, 4, 2, 14)): LowHandType.H_7542A,
    hash((7, 5, 4, 3, 14)): LowHandType.H_7543A,
    hash((7, 5, 4, 3, 2)): LowHandType.H_75432,

    hash((7, 6, 3, 2, 14)): LowHandType.H_7632A,
    hash((7, 6, 4, 2, 14)): LowHandType.H_7642A,
    hash((7, 6, 4, 3, 14)): LowHandType.H_7643A,
    hash((7, 6, 4, 3, 2)): LowHandType.H_76432,
    hash((7, 6, 5, 2, 14)): LowHandType.H_7652A,
    hash((7, 6, 5, 3, 14)): LowHandType.H_7653A,
    hash((7, 6, 5, 3, 2)): LowHandType.H_76532,
    hash((7, 6, 5, 4, 14)): LowHandType.H_7654A,
    hash((7, 6, 5, 4, 2)): LowHandType.H_76542,
    hash((7, 6, 5, 4, 3)): LowHandType.H_76543,

    # low 8
    hash((8, 4, 3, 2, 14)): LowHandType.H_8432A,

    hash((8, 5, 3, 2, 14)): LowHandType.H_8532A,
    hash((8, 5, 4, 2, 14)): LowHandType.H_8542A,
    hash((8, 5, 4, 3, 14)): LowHandType.H_8543A,
    hash((8, 5, 4, 3, 2)): LowHandType.H_85432,

    hash((8, 6, 3, 2, 14)): LowHandType.H_8632A,
    hash((8, 6, 4, 2, 14)): LowHandType.H_8642A,
    hash((8, 6, 4, 3, 14)): LowHandType.H_8643A,
    hash((8, 6, 4, 3, 2)): LowHandType.H_86432,
    hash((8, 6, 5, 2, 14)): LowHandType.H_8652A,
    hash((8, 6, 5, 3, 14)): LowHandType.H_8653A,
    hash((8, 6, 5, 3, 2)): LowHandType.H_86532,
    hash((8, 6, 5, 4, 14)): LowHandType.H_8654A,
    hash((8, 6, 5, 4, 2)): LowHandType.H_86542,
    hash((8, 6, 5, 4, 3)): LowHandType.H_86543,

    hash((8, 7, 3, 2, 14)): LowHandType.H_8732A,
    hash((8, 7, 4, 2, 14)): LowHandType.H_8742A,
    hash((8, 7, 4, 3, 14)): LowHandType.H_8743A,
    hash((8, 7, 4, 3, 2)): LowHandType.H_87432,
    hash((8, 7, 5, 2, 14)): LowHandType.H_8752A,
    hash((8, 7, 5, 3, 14)): LowHandType.H_8753A,
    hash((8, 7, 5, 3, 2)): LowHandType.H_87532,
    hash((8, 7, 5, 4, 14)): LowHandType.H_8754A,
    hash((8, 7, 5, 4, 2)): LowHandType.H_87542,
    hash((8, 7, 5, 4, 3)): LowHandType.H_87543,
    hash((8, 7, 6, 2, 14)): LowHandType.H_8762A,
    hash((8, 7, 6, 3, 14)): LowHandType.H_8763A,
    hash((8, 7, 6, 3, 2)): LowHandType.H_87632,
    hash((8, 7, 6, 4, 14)): LowHandType.H_8764A,
    hash((8, 7, 6, 4, 2)): LowHandType.H_87642,
    hash((8, 7, 6, 4, 3)): LowHandType.H_87643,
    hash((8, 7, 6, 5, 14)): LowHandType.H_8765A,
    hash((8, 7, 6, 5, 2)): LowHandType.H_87652,
    hash((8, 7, 6, 5, 3)): LowHandType.H_87653,
    hash((8, 7, 6, 5, 4)): LowHandType.H_87654,
}


class Hand:
    def __init__(self, cards, board: Board, deck36=False) -> None:
        self.cards = [x if isinstance(x, Card) else Card(x) for x in cards]
        self.cards.sort(key=lambda x: (-x.rank, x.suit))
        self.mask = 0
        for c in self.cards:
            self.mask |= c.mask
        self.type = self.get_type(deck36) if self.cards else None
        self.rank = None
        self.value = 0
        self.board = board

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


class LowHand(Hand):
    def __init__(self, cards):
        super().__init__(cards)

    def get_type(self, deck36=False):
        # проверяем есть ли вообще смысл считать low_type
        if not len(card_ranks := [card_rank for card_rank in set([card.rank for card in self.cards])
                                  if card_rank <= 8 or card_rank == 14]) == 5:
            return None

        # получаем индекс силы
        card_ranks = sorted(card_ranks, reverse=True)
        if 14 in card_ranks:
            card_ranks = card_ranks[1:] + card_ranks[:1]
        card_ranks = tuple(card_ranks)

        return low_hands_hashes.get(hash(card_ranks)), *card_ranks
