import pytest

from ravvi_poker.engine.poker.hands import Hand


@pytest.mark.asyncio
async def test_low_combinations():
    cards = ["5♠", "4♠", "3♠", "2♠", "A♣"]
    hand = Hand(cards)
    hand.get_low_type()
    raise ValueError
