from ravvi_poker_backend.game.cards import Card, Hand

def test_01_cards():
    # 2S
    c = Card(1)
    assert c.code == 1
    assert c.mask == 0b0000000000000000000000000000000000000000000000000001
    assert c.rank == 2
    assert c.suit_idx == 0

    # TS
    c = Card(13)
    assert c.code == 13
    assert c.mask == 0b0000000000000000000000000000000000000001000000000000
    assert c.rank == 14
    assert c.suit_idx == 0

    # 2C
    c = Card(14)
    assert c.code == 14
    assert c.mask == 0b0000000000000000000000000000000000000010000000000000
    assert c.rank == 2
    assert c.suit_idx == 1

    # TC
    c = Card(26)
    assert c.code == 26
    assert c.mask == 0b0000000000000000000000000010000000000000000000000000
    assert c.rank == 14
    assert c.suit_idx == 1

    # 2D
    c = Card(27)
    assert c.code == 27
    assert c.mask == 0b0000000000000000000000000100000000000000000000000000
    assert c.rank == 2
    assert c.suit_idx == 2

    # TD
    c = Card(39)
    assert c.code == 39
    assert c.mask == 0b0000000000000100000000000000000000000000000000000000
    assert c.rank == 14
    assert c.suit_idx == 2

    # 2H
    c = Card(40)
    assert c.code == 40
    assert c.mask == 0b0000000000001000000000000000000000000000000000000000
    assert c.rank == 2
    assert c.suit_idx == 3

    # TH
    c = Card(52)
    assert c.code == 52
    assert c.mask == 0b1000000000000000000000000000000000000000000000000000
    assert c.rank == 14
    assert c.suit_idx == 3

def test_02_hand():
    h = Hand([1, 14, 27, 39, 52])
    assert h.mask == 0b1000000000000100000000000100000000000010000000000001
