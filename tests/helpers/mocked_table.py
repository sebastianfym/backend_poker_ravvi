from unittest.mock import AsyncMock

from ravvi_poker.engine.poker.bomb_pot import BombPotController
from ravvi_poker.engine.poker.seven_deuce import SevenDeuceController


class MockedTable(AsyncMock):
    def __init__(self, seven_deuce: SevenDeuceController | None = None, bomb_pot: BombPotController | None = None):
        super().__init__()

        self.seven_deuce = seven_deuce
        self.bomb_pot = bomb_pot
