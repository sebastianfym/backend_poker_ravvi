import logging
from unittest.mock import AsyncMock

import pytest
from tests.helpers.x_game_case import load_game_cases, create_game_case
from tests.helpers.mocked_table import MockedTable

from ravvi_poker.engine.poker.base import PokerBase

logger = logging.getLogger(__name__)

X_Game = create_game_case(PokerBase)


def pytest_generate_tests(metafunc):
    if "game_case" in metafunc.fixturenames:
        metafunc.parametrize("game_case", load_game_cases(__file__))


@pytest.mark.asyncio
async def test_case(game_case):
    name, kwargs = game_case

    X_Game.GAME_TYPE = 'TEST'
    X_Game.GAME_SUBTYPE = 'TEST'

    mocked_table = MockedTable()
    game = X_Game(mocked_table, **kwargs)
    await game.run()
    assert not game._check_steps
