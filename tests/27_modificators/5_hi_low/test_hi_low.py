import pytest
from ravvi_poker.engine.poker.board import Board, BoardType

from ravvi_poker.engine.poker.hands import Hand, LowHand

from tests.helpers.x_game_case import load_game_cases, create_game_case
from tests.helpers.mocked_table import MockedTable

from ravvi_poker.engine.poker.hi_low import HiLowMixin
from ravvi_poker.engine.poker.plo import Poker_PLO_4


@pytest.mark.asyncio
async def test_low_combinations():
    board = Board(BoardType.BOARD1)
    cards = ["5♠", "4♠", "3♠", "2♠", "A♣"]
    hand = LowHand(cards, board)
    assert hand.get_type() is not None



def pytest_generate_tests(metafunc):
    if "game_case" in metafunc.fixturenames:
        metafunc.parametrize("game_case", load_game_cases(__file__))


X_Game = create_game_case(Poker_PLO_4)

class TestBombPot_NLX_RG:
    @pytest.mark.asyncio
    async def test_case(self, game_case):
        name, kwargs = game_case

        mocked_table = MockedTable()
        game = X_Game(mocked_table, **kwargs)
        game.__class__ = type(game.__class__.__name__, (HiLowMixin, game.__class__), {})
        await game.run()
        assert not game._check_steps

