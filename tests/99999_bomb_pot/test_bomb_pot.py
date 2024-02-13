from unittest.mock import AsyncMock

import pytest

from ravvi_poker.engine.poker.double_board import DoubleBoardMixin
from ravvi_poker.engine.poker.bomb_pot import BombPotMixin
from ravvi_poker.engine.poker.nlh import Poker_NLH_REGULAR
from helpers.x_game_case import load_game_cases, create_game_case


def pytest_generate_tests(metafunc):
    if "game_case" in metafunc.fixturenames:
        metafunc.parametrize("game_case", load_game_cases(__file__))


X_Game = create_game_case(Poker_NLH_REGULAR)


class TestBobPot_NLX_RG:
    @pytest.mark.asyncio
    async def test_case(self, game_case):
        name, kwargs = game_case

        mocked_table = AsyncMock()
        game = X_Game(mocked_table, **kwargs)
        game.__class__ = type(game.__class__.__name__, (BombPotMixin, game.__class__), {})
        if "double-board" in game_case[0]:
            game.__class__ = type(game.__class__.__name__, (DoubleBoardMixin, game.__class__), {})
        await game.run()
        assert not game._check_steps