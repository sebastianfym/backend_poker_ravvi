import pytest

from ravvi_poker.engine.poker.ante import AnteUpController
from ravvi_poker.engine.tables import Table_RG


@pytest.mark.asyncio
async def test_ante_params_exist():
    """
        Проверяем что если настройка анте выставлена, то мы увидим инициализированный инстанс анте
    """
    TABLE_ID = 777
    TABLE_NAME = "test_table"

    table = Table_RG(TABLE_ID, TABLE_NAME, table_seats=3,
                     props={
                         "ante_up": True
                     })

    assert isinstance(getattr(table, "ante"), AnteUpController)


@pytest.mark.asyncio
@pytest.mark.parametrize("ante_up", [None, False])
async def test_ante_params_not_exist(ante_up):
    """
        Проверяем что если настройка анте не выставлена или выставлена в False, то мы не увидим инициализированный
        инстанс анте
    """
    TABLE_ID = 777
    TABLE_NAME = "test_table"

    table = Table_RG(TABLE_ID, TABLE_NAME, table_seats=3,
                     props={
                         "ante_up": False
                     })

    assert getattr(table, "ante") is None


@pytest.mark.asyncio
@pytest.mark.parametrize("game_type,game_subtype",
                         [
                             ["NLH", "REGULAR"],
                         ])
async def test_initial_ante_value(game_type: str, game_subtype: str):
    TABLE_ID = 777
    TABLE_NAME = "test_table"

    table = Table_RG(TABLE_ID, TABLE_NAME, table_seats=3, game_type=game_type, game_subtype=game_subtype,
                     props={
                         "ante_up": True,
                         "blind_small": 0.05
                     })
    game = await table.game_factory([])

    assert game.current_ante_value == round(0.05 * 2 * 0.2, 2)
