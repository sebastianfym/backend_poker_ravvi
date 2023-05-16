from itertools import combinations
from time import time_ns

rank_map = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
suit_map = ['S','C','D','H'] # Spades(♠) Clubs (♣) Diamonds (♦) Hearts (♥) 
nranks = len(rank_map)


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
    
class Hand:
    
    def __init__(self, hand) -> None:
        self.hand = [Card(x) for x in hand]
        self.mask = 0
        for c in self.hand:
            self.mask |= c.mask

    def __str__(self) -> str:
        s = ' '.join([str(c) for c in reversed(self.hand)])
        return s
    
    
    def check_flash(self):
        for si in range(4):
            si *= 13
            match = self.mask & (0b1111111111111<<si)
            match >>= si
            bs = reversed(bin(match)[2:])
            cards = [i+1 for i, b in enumerate(bs) if b=='1']
            if len(cards)==5:
                cards.reverse()
                return cards
        return None


    def check_street(self):
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
                return i
        return 0
    

    def check_street_flash(self):
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
        result = []
        mask = 0
        for si in range(4):
            mask |= 1<<si*13
        for ri in range(13):
            hand = self.mask<<ri
            match = hand & mask
            counter = bin(match).count('1')
            if counter>1:
                result.append((counter, ri+1))
        if len(result)==1:
            c, r = result[0]
            if c==4:
                return 'K', r, 0
            elif c==3:
                return 'T', r, 0
            elif c==2:
                return 'P', r, 0
            else:
                raise ValueError('error')
        elif len(result)==2:
            result.sort(reverse=True)
            c, r = result[0]
            c2, r2 = result[1]
            if c==3 and c2==2:
                return 'FH', r, r2
            elif c==2 and c2==2:
                return 'P2', r, r2
            else:
                raise ValueError('error')
        return None


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
    street = hand.check_street()
    if flash and street:
        print(hand, flash, street)

    continue
    street_flash_rank = hand.check_street_flash()
    if street_flash_rank:
        street_flash_count += 1
        print(hand, 'SF', street_flash_rank)
        continue
    sr = hand.check_same_rank()
    if sr:
        print(hand, sr)
t1 = time_ns()
print(street_flash_count)
print((t1-t0)/len(c))
