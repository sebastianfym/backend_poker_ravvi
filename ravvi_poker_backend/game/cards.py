from itertools import combinations
from time import time_ns
from enum import IntEnum, unique

class Card:

    rank_map = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    suit_map = ['S','C','D','H'] # Spades(♠) Clubs (♣) Diamonds (♦) Hearts (♥) 
    suit_s_map = ['♠','♣','♦','♥']
    
    def __init__(self, card_id) -> None:
        self.code = card_id
        self.rank_idx = (self.code-1)%13
        self.suit_idx = int((self.code-1)/13)

    @property
    def mask(self):
        return 1 << self.code-1
    
    @property
    def rank(self):
        return self.rank_idx+2
    
    def __str__(self) -> str:
        return f"{self.rank_map[self.rank_idx]}{self.suit_s_map[self.suit_idx]}"

class HandRank(IntEnum):
    HIGH_CARD = 1
    ONE_PAIR = 2
    TWO_PAIR = 3
    THREE_OF_KIND = 4
    STRAIGHT = 5
    FLUSH = 6
    FULL_HOUSE = 7
    FOUR_OF_KIND = 8
    STRAIGHT_FLUSH = 9


class Hand:
    
    def __init__(self, hand) -> None:
        self.hand = [Card(x) if isinstance(x,int) else x for x in hand]
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
        for si in range(4):
            si *= 13
            match = self.mask & (0b1111111111111<<si)
            match >>= si
            bs = reversed(bin(match)[2:])
            cards = [i+1 for i, b in enumerate(bs) if b=='1']
            if len(cards)==5:
                cards.reverse()
                return HandRank.FLUSH, *cards
        return None


    def check_straight(self):
        flash_masks = [
            0b1000000001111, # 04
            0b0000000011111, # 05
            0b0000000111110, # 06
            0b0000001111100, # 07
            0b0000011111000, # 08
            0b0000111110000, # 09
            0b0001111100000, # 10
            0b0011111000000, # 11
            0b0111110000000, # 12
            0b1111100000000  # 13
        ]
        rank_mask = 0
        for si in range(4):
            si *= 13
            rank_mask |= (self.mask & (0b1111111111111<<si)) >> si
        for i, mask in enumerate(flash_masks, 4):
            if rank_mask & mask == mask:
                return HandRank.STRAIGHT, i
        return None
    

    def check_straight_flash(self):
        flash_masks = [
            0b1000000001111, # 04
            0b0000000011111, # 05
            0b0000000111110, # 06
            0b0000001111100, # 07
            0b0000011111000, # 08
            0b0000111110000, # 09
            0b0001111100000, # 10
            0b0011111000000, # 11
            0b0111110000000, # 12
            0b1111100000000  # 13
        ]
        for si in range(4):
            for i, mask in enumerate(flash_masks, 4):
                mask <<= si*13
                if self.mask & mask == mask:
                    return i
        return 0
    
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
    t0 = time_ns()
    cards = player_cards+game_cards
    results = []
    for h in combinations(cards, 5):
        hand = Hand(h)
        hand.rank = hand.check_hand()
        results.append(hand)
    results.sort(reverse=True, key=lambda x: x.rank)
    t1 = time_ns()
    return results[0]

def brutforce():
    cards = list(range(1, 53))
    for x in cards:
        c = Card(x)
        print(f"{x:02d} {str(c)} {c.mask:052b}")


    c = list(combinations(cards, 5))
    street_flash_count = 0
    has_pairs_count = 0
    t0 = time_ns()
    for h in c:
        hand = Hand(h)
        flash = hand.check_flash()
        street = hand.check_straight()
        if street and flash:
            street_flash_count += 1
        same_rank = hand.check_same_rank()
        #print(hand, flash, street, same_rank)
    t1 = time_ns()
    print(street_flash_count)
    print((t1-t0)/len(c))

def random_hand():
    import random
    cards = list(range(1, 53))
    random.shuffle(cards)

    t0 = time_ns()
    gcards = cards[:7]
    results = []
    for h in combinations(gcards, 5):
        hand = Hand(h)
        rank = hand.check_hand()
        #print(hand, hand.cards, rank)
        results.append((hand,rank))
    results.sort(reverse=True, key=lambda x: x[1])
    t1 = time_ns()

    for hand, rank in results:
        print(hand, hand.cards, rank)

    print((t1-t0)/1000000000)

def test_hand():
    h = Hand([1, 2, 3, 4, 5])
    print(h)
    result = h.check_hand()
    print(result)


if __name__=="__main__":
    random_hand()