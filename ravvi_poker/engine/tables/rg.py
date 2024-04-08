import asyncio
import decimal
import time
from decimal import Decimal, ROUND_HALF_DOWN

from psycopg.rows import Row

from . import TableStatus
from .base import Table, DBI
from ..events import Message
from ..user import User


class Table_RG(Table):
    TABLE_TYPE = "RG"

    def parse_props(self, buyin_min=1, buyin_max=10, blind_small: Decimal = Decimal("0.01"),
                    blind_big: Decimal | None = None, ante_up: bool | None = None,
                    action_time=30, **kwargs):
        from ..poker.ante import AnteUpController
        from ..poker.bomb_pot import BombPotController
        from ..poker.seven_deuce import SevenDeuceController

        if buyin_max is None:
            buyin_max = buyin_min*2;
        self.buyin_min = Decimal(buyin_min).quantize(Decimal("0.01"))
        self.buyin_max = Decimal(buyin_max).quantize(Decimal("0.01"))
        self.game_props.update(bet_timeout=action_time,
                               blind_small=Decimal(blind_small).quantize(Decimal("0.01")),
                               blind_big=Decimal(blind_big).quantize(Decimal("0.01")) if blind_big is not None
                               else blind_small * 2)

        if ante_up:
            self.ante = AnteUpController(self.game_props.get("blind_small"))
            if len(self.ante.ante_levels) != 0:
                self.game_props.update(ante=self.ante.current_ante_value)
        if bompot_settings := getattr(self, "game_modes_config").bombpot_settings:
            self.bombpot = BombPotController(bompot_settings)
            # TODO согласовать что отправлять
        if seven_deuce := getattr(self, "game_modes_config").seven_deuce:
            self.seven_deuce = SevenDeuceController(seven_deuce, self.game_props.get("blind_big"))
            # TODO согласовать что отправлять

    @property
    def user_enter_enabled(self):
        return True

    @property
    def user_exit_enabled(self):
        return True

