from time import time_ns
from itertools import combinations
from ravvi_poker.game.cards import Card, Hand, HandRank

def brutforce():
    cards = list(range(1, 53))
    for x in cards:
        c = Card(x)
        print(f"{x:02d} {str(c)} {c.mask:052b}")


    c = list(combinations(cards, 5))
    street_flush_count = 0
    has_pairs_count = 0
    t0 = time_ns()
    for h in c:
        hand = Hand(h)
        flush = hand.check_flush()
        street = hand.check_straight()
        if street and flush:
            street_flush_count += 1
        same_rank = hand.check_same_rank()
        #print(hand, flush, street, same_rank)
    t1 = time_ns()
    print(street_flush_count)
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
        rank = hand.get_rank()
        #print(hand, hand.cards, rank)
        results.append((hand,rank))
    results.sort(reverse=True, key=lambda x: x[1])
    t1 = time_ns()

    for hand, rank in results:
        print(hand, hand.cards, rank)

    print((t1-t0)/1000000000)

#"♠", "♣", "♦", "♥"
def test_hand():
    h = Hand(["2♠", "2♣", "3♥", "4♥"])
    print(h)
    result = h.get_rank()
    print(result)


if __name__=="__main__":
    test_hand()