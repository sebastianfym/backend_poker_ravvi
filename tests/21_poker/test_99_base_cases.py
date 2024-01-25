import logging
import asyncio
from unittest.mock import MagicMock, PropertyMock, AsyncMock

import pytest
from ravvi_poker.engine.poker.base import PokerBase

from helpers.x_game_case import load_game_cases, create_game_case
from helpers.x_dbi import X_DBI
from helpers.x_table import X_Table
from ravvi_poker.engine.events import Command

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

    table_mock = AsyncMock()
    table_mock.game_type = X_Game.GAME_TYPE
    table_mock.game_subtype = X_Game.GAME_SUBTYPE
    table_mock.game_props = {"blind_value": 1, "ante": 5, "current_ante": 10, "ante_up": False}
    user_mock = MagicMock()
    user_mock.id = 5
    user_mock.get_info.return_value = {"id": 1, "name": "TestName"}
    table_mock.seats = [user_mock]
    game = X_Game(table_mock, **kwargs)
    await game.run()
    assert not game._check_steps
