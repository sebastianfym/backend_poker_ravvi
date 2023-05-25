from itertools import combinations
from enum import IntEnum, unique

class Card:

    rank_map = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    suit_map = ['S','C','D','H'] # Spades(♠) Clubs (♣) Diamonds (♦) Hearts (♥) 
    suit_s_map = ['♠','♣','♦','♥']
    
    def __init__(self, code=None, *, rank=None, suit=None) -> None:
        if code is None:
            code = self.encode(rank, suit)
        assert 0 <= code and code <= 52
        self.code = code
        if self.code:
            self.rank_idx = (self.code-1)%13
            self.suit_idx = int((self.code-1)/13)
        else:
            self.rank_idx = None

    @classmethod
    def encode(cls, rank, suit):
        assert 2 <= rank and rank <= 14
        assert 1 <= suit and suit <= 4
        return (suit-1)*13 + (rank-1)

    @property
    def rank(self):
        if 1 <= self.code and self.code <= 52:
            return (self.code-1)%13+2
        else:
            return 0
    
    @property
    def suit(self):
        if 1 <= self.code and self.code <= 52:
            return int((self.code-1)/13)+1
        else:
            return 0
    
    @property
    def mask(self):
        return 1 << self.code-1 if self.code else 0
    
    def __str__(self) -> str:
        return f"{self.rank_map[self.rank_idx]}{self.suit_s_map[self.suit_idx]}"

@unique
class HandRank(IntEnum):
    HIGH_CARD = 1
    ONE_PAIR = 2
    TWO_PAIR = 3
    THREE_OF_KIND = 4
    STRAIGHT = 5
    FLASH = 6
    FULL_HOUSE = 7
    FOUR_OF_KIND = 8
    STRAIGHT_FLUSH = 9


class Hand:
    
    def __init__(self, hand) -> None:
        self.hand = [x if isinstance(x,Card) else Card(x) for x in hand]
        self.mask = 0
        for c in self.hand:
            self.mask |= c.mask

    def __str__(self) -> str:
        s = ' '.join([str(c) for c in reversed(self.hand)])
        return s
    
    @property
    def cards(self):
        cards = [c for c in self.hand]
        cards.sort(reverse=True, key=lambda x: x.rank)
        return [c.code for c in cards]

    def get_cards_by_rank_reversed(self):
        cards = [c for c in self.hand]
        cards.sort(reverse=True, key=lambda x: x.rank)
        return cards
    
    def check_hand(self):
        flash = self.check_flash()
        straight = self.check_straight()
        if flash and straight:
            return HandRank.STRAIGHT_FLUSH, straight[1]
        elif flash:
            return flash
        elif straight:
            return straight
        return self.check_same_rank()

    def check_flash(self):
        for suit_index in range(4):
            suit_index *= 13
            suit_mask = (self.mask >> suit_index) & 0b1111111111111
            match = bin(suit_mask)[2:]
            cards_rank = [i for i, b in enumerate(reversed(match), 2) if b=='1']
            if len(cards_rank)==5:
                return HandRank.FLASH, max(cards_rank)
        return None


    def check_straight(self):
        flash_masks = [
            0b1000000001111, # 05
            0b0000000011111, # 06
            0b0000000111110, # 07
            0b0000001111100, # 08
            0b0000011111000, # 09
            0b0000111110000, # 10
            0b0001111100000, # 11
            0b0011111000000, # 12
            0b0111110000000, # 13
            0b1111100000000  # 14
        ]
        rank_mask = 0
        for suit_index in range(4):
            suit_index *= 13
            suit_mask = (self.mask >> suit_index) & 0b1111111111111            
            rank_mask |= suit_mask
        for i, mask in enumerate(flash_masks, 5):
            if rank_mask & mask == mask:
                return HandRank.STRAIGHT, i
        return None
    
    def check_same_rank(self):
        cards = list(self.hand)
        result = []
        mask = 0
        for _ in range(4):
            mask = mask << 13
            mask |= 1
        for rank_idx in range(0, 13):
            hm = mask<<rank_idx
            match = self.mask & hm
            counter = bin(match).count('1')
            if counter>1:
                result.append((counter, rank_idx+1))
        for _, rank in result:
            cards = [c for c in cards if c.rank!=rank]
        cards.sort(reverse=True, key=lambda x: x.rank)
        cards = [c.code for c in cards]
        if len(result)==1:
            counter, rank = result[0]
            if counter==4:
                return HandRank.FOUR_OF_KIND, rank, *cards
            elif counter==3:
                return HandRank.THREE_OF_KIND, rank, *cards
            elif counter==2:
                return HandRank.ONE_PAIR, rank, *cards
            else:
                raise ValueError('error')
        elif len(result)==2:
            result.sort(reverse=True)
            c1, r1 = result[0]
            c2, r2 = result[1]
            if c1==3 and c2==2:
                return HandRank.FULL_HOUSE, r1, r2, *cards
            elif c1==2 and c2==2:
                return HandRank.TWO_PAIR, r1, r2, *cards
            else:
                raise ValueError('error')
        return HandRank.HIGH_CARD, *cards

def get_player_best_hand(player_cards, game_cards):
    cards = player_cards+game_cards
    results = []
    for h in combinations(cards, 5):
        hand = Hand(h)
        hand.rank = hand.check_hand()
        results.append(hand)
    results.sort(reverse=True, key=lambda x: x.rank)
    return results[0]
