from ravvi_poker.game.cards import Card, Hand, HandRank

def test_01_cards():


    c = Card(0)
    assert c.code == 0
    assert c.mask == 0
    assert c.rank == 0
    assert c.suit == 0

    # 2S
    code = Card.encode(2, 1)
    assert code == 1

    c = Card(code)
    assert c.code == 1
    assert c.mask == 0b0000000000000000000000000000000000000000000000000001
    assert c.rank == 2
    assert c.suit == 1

    # TS
    code = Card.encode(14, 1)
    assert code == 13

    c = Card(code)
    assert c.code == 13
    assert c.mask == 0b0000000000000000000000000000000000000001000000000000
    assert c.rank == 14
    assert c.suit == 1

    # 2C
    code = Card.encode(2, 2)
    assert code == 14

    c = Card(code)
    assert c.code == 14
    assert c.mask == 0b0000000000000000000000000000000000000010000000000000
    assert c.rank == 2
    assert c.suit == 2

    # TC
    code = Card.encode(14, 2)
    assert code == 26

    c = Card(code)
    assert c.code == 26
    assert c.mask == 0b0000000000000000000000000010000000000000000000000000
    assert c.rank == 14
    assert c.suit == 2

    # 2D
    code = Card.encode(2, 3)
    assert code == 27

    c = Card(code)
    assert c.code == 27
    assert c.mask == 0b0000000000000000000000000100000000000000000000000000
    assert c.rank == 2
    assert c.suit == 3

    # TD
    code = Card.encode(14, 3)
    assert code == 39

    c = Card(code)
    assert c.code == 39
    assert c.mask == 0b0000000000000100000000000000000000000000000000000000
    assert c.rank == 14
    assert c.suit == 3

    # 2H
    code = Card.encode(2, 4)
    assert code == 40

    c = Card(code)
    assert c.code == 40
    assert c.mask == 0b0000000000001000000000000000000000000000000000000000
    assert c.rank == 2
    assert c.suit == 4

    # TH
    code = Card.encode(14, 4)
    assert code == 52

    c = Card(code)
    assert c.code == 52
    assert c.mask == 0b1000000000000000000000000000000000000000000000000000
    assert c.rank == 14
    assert c.suit == 4


def test_02_hand():
    h = Hand([1, 14, 27, 39, 52])
    assert h.mask == 0b1000000000000100000000000100000000000010000000000001

    h = Hand([1, 14, 27, 32, 39, 52])
    assert h.mask == 0b1000000000000100000010000100000000000010000000000001


def test_02_flash():
    cards = [
        Card(rank=14, suit=1),
        Card(rank=12, suit=2),
        Card(rank=10, suit=1),
        Card(rank=8, suit=1),
        Card(rank=6, suit=1)
    ]

    h = Hand(cards)
    result  = h.check_flash()
    assert result is None

    cards = [
        Card(rank=14, suit=1),
        Card(rank=12, suit=1),
        Card(rank=10, suit=1),
        Card(rank=8, suit=1),
        Card(rank=6, suit=1)
    ]

    h = Hand(cards)
    result  = h.check_flash()
    assert result == (HandRank.FLASH, 14)

    cards = [
        Card(rank=9, suit=4),
        Card(rank=7, suit=4),
        Card(rank=5, suit=4),
        Card(rank=4, suit=4),
        Card(rank=2, suit=4)
    ]

    h = Hand(cards)
    result  = h.check_flash()
    assert result == (HandRank.FLASH, 9)

def test_03_straight():
    cards = [
        Card(rank=14, suit=1),
        Card(rank=2, suit=2),
        Card(rank=8, suit=3),
        Card(rank=4, suit=4),
        Card(rank=5, suit=1)
    ]

    h = Hand(cards)
    result  = h.check_straight()
    assert result is None

    cards = [
        Card(rank=14, suit=1),
        Card(rank=2, suit=2),
        Card(rank=3, suit=3),
        Card(rank=4, suit=4),
        Card(rank=5, suit=1)
    ]

    h = Hand(cards)
    result  = h.check_straight()
    assert result == (HandRank.STRAIGHT, 5)

    cards = [
        Card(rank=14, suit=1),
        Card(rank=13, suit=2),
        Card(rank=12, suit=3),
        Card(rank=11, suit=4),
        Card(rank=10, suit=1)
    ]

    h = Hand(cards)
    result  = h.check_straight()
    assert result == (HandRank.STRAIGHT, 14)

def test_04_same_rank():
    cards = [
        Card(rank=14, suit=1),
        Card(rank=2, suit=2),
        Card(rank=8, suit=3),
        Card(rank=4, suit=4),
        Card(rank=5, suit=1)
    ]

    h = Hand(cards)
    result  = h.check_same_rank()
