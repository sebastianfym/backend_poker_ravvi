import pytest
from ravvi_poker.game.cards import Card, get_deck_52, get_deck_36

def test_01_1_cards():
    c = Card(0)
    assert c.code == 0
    assert c.mask == 0
    assert c.rank is None
    assert c.suit is None
    assert str(c) == "XX"

    def iter_deck():
        code = 1
        for si, sn in enumerate(Card.SUITS):
            ss = Card.SUITS2[si]
            for ri, rn in enumerate(Card.RANKS):
                yield code, f"{rn}{sn}", f"{rn}{ss}", sn, ss, si+1, rn, ri+2
                code += 1

    for code, cs1, cs2, sn, ss, si, rn, ri in iter_deck():
        print(code, cs1, cs2, sn, ss, si, rn, ri)
        for x in [code, cs1, cs2]:
            c = Card(x)
            assert c.code == code
            assert c.mask != 0
            assert c.suit == si
            assert c.rank == ri

        for s in [sn, ss, si]:
            for r in [rn, ri]:
                c = Card(suit=s, rank=r)
                assert c.code == code
                assert c.mask != 0
                assert c.suit == si
                assert c.rank == ri

def test_01_2_cards_negative():
    with pytest.raises(ValueError):
        c = Card(-1)
    with pytest.raises(ValueError):
        c = Card(53)
    with pytest.raises(ValueError):
        c = Card("XX")
    with pytest.raises(ValueError):
        c = Card("XXX")
    with pytest.raises(ValueError):
        c = Card(suit=0, rank=2)
    with pytest.raises(ValueError):
        c = Card(suit=5, rank=2)
    with pytest.raises(ValueError):
        c = Card(suit="X", rank=2)
    with pytest.raises(ValueError):
        c = Card(suit=1, rank=1)
    with pytest.raises(ValueError):
        c = Card(suit=1, rank=15)
    with pytest.raises(ValueError):
        c = Card(suit=1, rank="X")

def test_01_3_cards_samples():

    # 2S
    c = Card("2S")
    assert c.code == 1
    assert c.mask == 0b0000000000000000000000000000000000000000000000000001
    assert c.rank == 2
    assert c.suit == 1
    assert str(c) == "2♠"

    # AS
    c = Card("AS")
    assert c.code == 13
    assert c.mask == 0b0000000000000000000000000000000000000001000000000000
    assert c.rank == 14
    assert c.suit == 1
    assert str(c) == "A♠"

    # 2C
    c = Card("2C")
    assert c.code == 14
    assert c.mask == 0b0000000000000000000000000000000000000010000000000000
    assert c.rank == 2
    assert c.suit == 2

    # AC
    c = Card("AC")
    assert c.code == 26
    assert c.mask == 0b0000000000000000000000000010000000000000000000000000
    assert c.rank == 14
    assert c.suit == 2

    # 2D
    c = Card("2D")
    assert c.code == 27
    assert c.mask == 0b0000000000000000000000000100000000000000000000000000
    assert c.rank == 2
    assert c.suit == 3

    # AD
    c = Card("AD")
    assert c.code == 39
    assert c.mask == 0b0000000000000100000000000000000000000000000000000000
    assert c.rank == 14
    assert c.suit == 3

    # 2H
    c = Card("2H")
    assert c.code == 40
    assert c.mask == 0b0000000000001000000000000000000000000000000000000000
    assert c.rank == 2
    assert c.suit == 4

    # AH
    c = Card("AH")
    assert c.code == 52
    assert c.mask == 0b1000000000000000000000000000000000000000000000000000
    assert c.rank == 14
    assert c.suit == 4

def test_01_4_deck_52():
    deck = get_deck_52()
    assert len(deck) == 52
    u = set(deck)
    assert len(u)==52
    for i, code in enumerate(deck, start=1):
        assert code == i

def test_01_5_deck_36():
    deck = get_deck_36()
    assert len(deck) == 36
    u = set(deck)
    assert len(u)==36
    for i, code in enumerate(deck):
        c = Card(code)
        assert c.rank>=6

#if __name__=="__main__":
#    test_01_1_cards()