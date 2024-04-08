from unittest.mock import AsyncMock, MagicMock

from ravvi_poker.engine.poker.bomb_pot import BombPotController
from ravvi_poker.engine.poker.seven_deuce import SevenDeuceController


class MockedTable(AsyncMock):
    def __init__(self, seven_deuce: SevenDeuceController | None = None, bomb_pot: BombPotController | None = None):
        super().__init__()

        self.seven_deuce = seven_deuce
        self.bomb_pot = bomb_pot
        game_modes_config = MagicMock()
        game_modes_config.players_required = 2
        self.game_modes_config = game_modes_config
