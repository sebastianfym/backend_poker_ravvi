from unittest.mock import MagicMock

import pytest

from ravvi_poker.engine.tables import Table


@pytest.mark.asyncio
async def test_compatibility_mixins():
    table = Table(1, "test", table_seats=6,
                  game_type="NLH", game_subtype="AOF",
                  props={"double_board": True})

    game = await table.game_factory([MagicMock(), MagicMock()])

