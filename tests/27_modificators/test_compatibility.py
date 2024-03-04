from unittest.mock import MagicMock

import pytest

from ravvi_poker.engine.game import Game
from ravvi_poker.engine.tables import Table_RG


@pytest.mark.asyncio
@pytest.mark.parametrize("game_type, game_subtype, is_support",
                         [
                             ["NLH", "AOF", False],

                             ["NLH", "REGULAR", True],
                             ["NLH", "3-1", True],
                             ["NLH", "6+", True],

                             ["PLO", "PLO4", True],
                             ["PLO", "PLO5", True],
                             ["PLO", "PLO6", True],
                         ])
async def test_compatibility_double_board(game_type, game_subtype, is_support):
    table = Table_RG(1, "test", table_seats=6,
                     game_type=game_type, game_subtype=game_subtype,
                     props={"double_board": True})

    if not is_support:
        with pytest.raises(ValueError) as err:
            await table.game_factory([MagicMock(), MagicMock()])
        assert "not support mode" in str(err.value)
    else:
        game = await table.game_factory([MagicMock(), MagicMock()])
        assert isinstance(game, Game)


@pytest.mark.asyncio
@pytest.mark.parametrize("game_type, game_subtype, is_support",
                         [
                             ["NLH", "AOF", False],

                             ["NLH", "REGULAR", True],
                             ["NLH", "3-1", True],
                             ["NLH", "6+", True],

                             ["PLO", "PLO4", True],
                             ["PLO", "PLO5", True],
                             ["PLO", "PLO6", True],
                         ])
async def test_compatibility_bombpot(game_type, game_subtype, is_support):
    table = Table_RG(1, "test", table_seats=6,
                  game_type=game_type, game_subtype=game_subtype,
                  props={"bombpot_freq": 1, "bombpot_min": 1, "bombpot_max": 2, "bombpot_double_board": False})

    if not is_support:
        with pytest.raises(ValueError) as err:
            await table.game_factory([MagicMock(), MagicMock()])
        assert "not support mode" in str(err.value)
    else:
        game = await table.game_factory([MagicMock(), MagicMock()])
        assert isinstance(game, Game)
