import logging
import asyncio
import pytest
from ravvi_poker.engine.poker.base import PokerBase

from helpers.x_game_case import load_game_cases, create_game_case

logger = logging.getLogger(__name__)

X_Game = create_game_case(PokerBase)

def pytest_generate_tests(metafunc):
    if "game_case" in metafunc.fixturenames:
        metafunc.parametrize("game_case", load_game_cases(__file__))

@pytest.mark.asyncio
async def test_case(game_case):
    name, kwargs = game_case

    X_Game.GAME_TYPE='TEST'
    X_Game.GAME_SUBTYPE='TEST'
    
    game = X_Game(None, **kwargs)
    await game.run()
    assert not game._check_steps