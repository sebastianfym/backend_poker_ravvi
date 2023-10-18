from ravvi_poker.game.hands import Card, Hand, HandRank, get_player_best_hand

def test_02_hand():
    h = Hand([1, 14, 27, 39, 52])
    assert h.mask == 0b1000000000000100000000000100000000000010000000000001

    h = Hand([1, 14, 27, 32, 39, 52])
    assert h.mask == 0b1000000000000100000010000100000000000010000000000001


def test_02_flush():
    cards = [
        Card(rank=14, suit=1),
        Card(rank=12, suit=2),
        Card(rank=10, suit=1),
        Card(rank=8, suit=1),
        Card(rank=6, suit=1)
    ]

    h = Hand(cards)
    result  = h.check_flush()
    assert result is None

    cards = [
        Card(rank=14, suit=1),
        Card(rank=12, suit=1),
        Card(rank=10, suit=1),
        Card(rank=8, suit=1),
        Card(rank=6, suit=1)
    ]

    h = Hand(cards)
    result  = h.get_rank()
    assert result == (HandRank.FLUSH, 14, 12, 10, 8, 6)

    cards = [
        Card(rank=9, suit=4),
        Card(rank=7, suit=4),
        Card(rank=5, suit=4),
        Card(rank=4, suit=4),
        Card(rank=2, suit=4)
    ]

    h = Hand(cards)
    result  = h.get_rank()
    assert result == (HandRank.FLUSH, 9, 7, 5, 4, 2)

def test_03_straight():
    cards = [
        Card(rank=14, suit=1),
        Card(rank=2, suit=2),
        Card(rank=8, suit=3),
        Card(rank=4, suit=4),
        Card(rank=5, suit=1)
    ]

    h = Hand(cards)
    result  = h.check_straight(cards36=False)
    assert result is None

    cards = [
        Card(rank=14, suit=1),
        Card(rank=2, suit=2),
        Card(rank=3, suit=3),
        Card(rank=4, suit=4),
        Card(rank=5, suit=1)
    ]

    h = Hand(cards)
    result  = h.get_rank()
    assert result == (HandRank.STRAIGHT, 5)

    cards = [
        Card(rank=14, suit=1),
        Card(rank=13, suit=2),
        Card(rank=12, suit=3),
        Card(rank=11, suit=4),
        Card(rank=10, suit=1)
    ]

    h = Hand(cards)
    result  = h.get_rank()
    assert result == (HandRank.STRAIGHT, 14)

def test_04_HIGH_CARD():
    cards = [
        Card(rank=14, suit=1),
        Card(rank=2, suit=2),
        Card(rank=8, suit=3),
        Card(rank=4, suit=4),
        Card(rank=5, suit=1)
    ]

    h = Hand(cards)
    result  = h.get_rank()
    assert result == (HandRank.HIGH_CARD, 14, 8, 5, 4, 2)

    cards = [
        Card(rank=9, suit=1),
        Card(rank=2, suit=2),
        Card(rank=8, suit=3),
        Card(rank=4, suit=2),
        Card(rank=3, suit=1)
    ]

    h = Hand(cards)
    result  = h.get_rank()
    assert result == (HandRank.HIGH_CARD, 9, 8, 4, 3, 2)

    cards = [
        Card(rank=14, suit=1),
        Card(rank=2, suit=2),
        Card(rank=8, suit=3),
        Card(rank=4, suit=4),
        Card(rank=5, suit=1)
    ]

    h = Hand(cards)
    result  = h.get_rank()
    assert result == (HandRank.HIGH_CARD, 14, 8, 5, 4, 2)


def test_05_ONE_PAIR():
    cards = [
        Card(rank=9, suit=1),
        Card(rank=2, suit=2),
        Card(rank=8, suit=3),
        Card(rank=2, suit=1),
        Card(rank=3, suit=1)
    ]

    h = Hand(cards)
    result  = h.get_rank()
    assert result == (HandRank.ONE_PAIR, 2, 9, 8, 3)

def test_06_THREE_OF_KIND():
    cards = [
        Card(rank=9, suit=1),
        Card(rank=2, suit=2),
        Card(rank=3, suit=3),
        Card(rank=2, suit=1),
        Card(rank=2, suit=3)
    ]

    h = Hand(cards)
    result  = h.get_rank()
    assert result == (HandRank.THREE_OF_KIND, 2, 9, 3)

def test_07_FOUR_OF_KIND():
    cards = [
        Card(rank=9, suit=1),
        Card(rank=2, suit=1),
        Card(rank=2, suit=2),
        Card(rank=2, suit=3),
        Card(rank=2, suit=4)
    ]

    h = Hand(cards)
    result  = h.get_rank()
    assert result == (HandRank.FOUR_OF_KIND, 2, 9)


def test_08_TWO_PAIR():
    cards = [
        Card(rank=9, suit=1),
        Card(rank=5, suit=1),
        Card(rank=5, suit=2),
        Card(rank=2, suit=3),
        Card(rank=2, suit=4)
    ]

    h = Hand(cards)
    result  = h.get_rank()
    assert result == (HandRank.TWO_PAIR, 5, 2, 9)

def test_09_FULL_HOUSE():
    cards = [
        Card(rank=5, suit=1),
        Card(rank=5, suit=2),
        Card(rank=5, suit=3),
        Card(rank=2, suit=3),
        Card(rank=2, suit=4)
    ]

    h = Hand(cards)
    result  = h.get_rank()
    assert result == (HandRank.FULL_HOUSE, 5, 2)

def test_10_ROYAL_FLUSH():
    cards = [
        Card(rank=14, suit=1),
        Card(rank=13, suit=1),
        Card(rank=12, suit=1),
        Card(rank=11, suit=1),
        Card(rank=10, suit=1)
    ]

    h = Hand(cards)
    result  = h.get_rank()
    assert result == (HandRank.STRAIGHT_FLUSH, 14)

def test_20_best_hand():
    player_cards = [
        Card(rank=14, suit=1),
        Card(rank=13, suit=1),
    ]

    game_cards = [
        Card(rank=12, suit=1),
        Card(rank=7, suit=3),
        Card(rank=3, suit=4),
        Card(rank=11, suit=1),
        Card(rank=10, suit=1)
    ]

    hand = get_player_best_hand(player_cards, game_cards)
    assert hand.rank == (HandRank.STRAIGHT_FLUSH, 14)

    assert str(hand) == "A♠ K♠ Q♠ J♠ T♠"
