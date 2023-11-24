import pytest

from ravvi_poker.engine.poker.hands import Hand, HandType


def test_hand_mask():
    cards = []
    hand = Hand(cards)
    assert hand.mask == 0
    assert hand.type is None

    hand = Hand([1, 14, 27, 40, 52])
    assert hand.mask == 0b1000000000001000000000000100000000000010000000000001
    assert str(hand) == "A♥ 2♠ 2♣ 2♦ 2♥"

    hand = Hand([1, 13, 26, 39, 52])
    assert hand.mask == 0b1000000000000100000000000010000000000001000000000001
    assert str(hand) == "A♠ A♣ A♦ A♥ 2♠"


def test_samples_HIGH_CARD():
    # "♠", "♣", "♦", "♥"
    cards = ["2♠"]
    hand = Hand(cards)
    assert hand.type == (HandType.HIGH_CARD, 2)
    assert str(hand) == "2♠"

    cards = ["2♠", "3♠"]
    hand = Hand(cards)
    assert hand.type == (HandType.HIGH_CARD, 3, 2)
    assert str(hand) == "3♠ 2♠"

    cards = ["3♠", "2♠"]
    hand = Hand(cards)
    assert hand.type == (HandType.HIGH_CARD, 3, 2)
    assert str(hand) == "3♠ 2♠"

    cards = ["3♠", "6♠", "2♠"]
    hand = Hand(cards)
    assert hand.type == (HandType.HIGH_CARD, 6, 3, 2)
    assert str(hand) == "6♠ 3♠ 2♠"

    cards = ["2♠", "9♣", "3♠", "6♠"]
    hand = Hand(cards)
    assert hand.type == (HandType.HIGH_CARD, 9, 6, 3, 2)
    assert str(hand) == "9♣ 6♠ 3♠ 2♠"

    cards = [
        "2♠",
        "A♣",
        "3♠",
        "6♠",
        "9♣",
    ]
    hand = Hand(cards)
    assert hand.type == (HandType.HIGH_CARD, 14, 9, 6, 3, 2)
    assert str(hand) == "A♣ 9♣ 6♠ 3♠ 2♠"


def test_samples_ONE_PAIR():
    # "♠", "♣", "♦", "♥"
    cards = ["2♠", "2♣"]
    hand = Hand(cards)
    assert hand.type == (HandType.ONE_PAIR, 2)
    assert str(hand) == "2♠ 2♣"

    cards = ["2♠", "2♣", "3♦"]
    hand = Hand(cards)
    assert hand.type == (HandType.ONE_PAIR, 2, 3)
    assert str(hand) == "3♦ 2♠ 2♣"

    cards = ["2♠", "7♥", "2♣", "3♦"]
    hand = Hand(cards)
    assert hand.type == (HandType.ONE_PAIR, 2, 7, 3)
    assert str(hand) == "7♥ 3♦ 2♠ 2♣"

    cards = ["2♠", "7♥", "A♥", "2♣", "3♦"]
    hand = Hand(cards)
    assert hand.type == (HandType.ONE_PAIR, 2, 14, 7, 3)
    assert str(hand) == "A♥ 7♥ 3♦ 2♠ 2♣"


def test_samples_TWO_PAIR():
    # "♠", "♣", "♦", "♥"

    cards = ["2♠", "2♣", "3♦", "3♣"]
    hand = Hand(cards)
    assert hand.type == (HandType.TWO_PAIRS, 3, 2)
    assert str(hand) == "3♣ 3♦ 2♠ 2♣"

    cards = ["2♠", "2♣", "3♦", "3♣", "A♥"]
    hand = Hand(cards)
    assert hand.type == (HandType.TWO_PAIRS, 3, 2, 14)
    assert str(hand) == "A♥ 3♣ 3♦ 2♠ 2♣"


def test_samples_THREE_OF_KIND():
    # "♠", "♣", "♦", "♥"

    cards = ["2♠", "2♣", "2♦"]
    hand = Hand(cards)
    assert hand.type == (HandType.THREE_OF_KIND, 2)
    assert str(hand) == "2♠ 2♣ 2♦"

    cards = ["2♠", "2♣", "3♣", "2♦"]
    hand = Hand(cards)
    assert hand.type == (HandType.THREE_OF_KIND, 2, 3)
    assert str(hand) == "3♣ 2♠ 2♣ 2♦"

    cards = ["2♠", "T♣", "2♣", "3♣", "2♦"]
    hand = Hand(cards)
    assert hand.type == (HandType.THREE_OF_KIND, 2, 10, 3)
    assert str(hand) == "T♣ 3♣ 2♠ 2♣ 2♦"


def test_samples_FOUR_OF_KIND():
    # "♠", "♣", "♦", "♥"

    cards = ["2♠", "2♣", "2♦", "2♥"]
    hand = Hand(cards)
    assert hand.type == (HandType.FOUR_OF_KIND, 2)
    assert str(hand) == "2♠ 2♣ 2♦ 2♥"

    cards = ["2♠", "2♣", "T♣", "2♦", "2♥"]
    hand = Hand(cards)
    assert hand.type == (HandType.FOUR_OF_KIND, 2, 10)
    assert str(hand) == "T♣ 2♠ 2♣ 2♦ 2♥"


def test_samples_FULL_HOUSE():
    # "♠", "♣", "♦", "♥"

    cards = ["2♠", "2♣", "T♣", "T♦", "2♥"]
    hand = Hand(cards)
    assert hand.type == (HandType.FULL_HOUSE, 2, 10)
    assert str(hand) == "T♣ T♦ 2♠ 2♣ 2♥"


def test_samples_52_STRAIGHT():
    cards = ["T♠", "A♣", "Q♣", "K♦", "J♥"]
    hand = Hand(cards, deck36=False)
    assert hand.type == (HandType.STRAIGHT, 14)
    assert str(hand) == "A♣ K♦ Q♣ J♥ T♠"

    cards = ["2♠", "A♣", "4♣", "5♦", "3♥"]
    hand = Hand(cards, deck36=False)
    assert hand.type == (HandType.STRAIGHT, 5)
    assert str(hand) == "A♣ 5♦ 4♣ 3♥ 2♠"


def test_samples_36_STRAIGHT():
    cards = ["T♠", "A♣", "Q♣", "K♦", "J♥"]
    hand = Hand(cards, deck36=True)
    assert hand.type == (HandType.STRAIGHT, 14)
    assert str(hand) == "A♣ K♦ Q♣ J♥ T♠"

    cards = ["6♠", "A♣", "8♣", "9♦", "7♥"]
    hand = Hand(cards, deck36=True)
    assert hand.type == (HandType.STRAIGHT, 9)
    assert str(hand) == "A♣ 9♦ 8♣ 7♥ 6♠"


def test_samples_FLUSH():
    cards = ["T♠", "2♠", "J♠", "4♠", "K♠"]
    hand = Hand(cards)
    assert hand.type == (HandType.FLUSH, 13, 11, 10, 4, 2)
    assert str(hand) == "K♠ J♠ T♠ 4♠ 2♠"

    cards = ["3♥", "2♥", "J♥", "4♥", "7♥"]
    hand = Hand(cards)
    assert hand.type == (HandType.FLUSH, 11, 7, 4, 3, 2)
    assert str(hand) == "J♥ 7♥ 4♥ 3♥ 2♥"


def test_samples_STRAIGHT_FLUSH():
    cards = ["6♠", "2♠", "3♠", "4♠", "5♠"]
    hand = Hand(cards)
    assert hand.type == (HandType.STRAIGHT_FLUSH, 6)
    assert str(hand) == "6♠ 5♠ 4♠ 3♠ 2♠"

    cards = ["7♥", "8♥", "J♥", "T♥", "9♥"]
    hand = Hand(cards)
    assert hand.type == (HandType.STRAIGHT_FLUSH, 11)
    assert str(hand) == "J♥ T♥ 9♥ 8♥ 7♥"

    cards = ["2♦", "A♦", "4♦", "5♦", "3♦"]
    hand = Hand(cards, deck36=False)
    assert hand.type == (HandType.STRAIGHT_FLUSH, 5)
    assert str(hand) == "A♦ 5♦ 4♦ 3♦ 2♦"

    cards = ["6♥", "A♥", "8♥", "9♥", "7♥"]
    hand = Hand(cards, deck36=True)
    assert hand.type == (HandType.STRAIGHT_FLUSH, 9)
    assert str(hand) == "A♥ 9♥ 8♥ 7♥ 6♥"
