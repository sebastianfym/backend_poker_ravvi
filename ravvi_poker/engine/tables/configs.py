from logging import getLogger

logger = getLogger(__name__)


class TableConfigParams:
    def __init__(self):
        pass

    def unpack_for_msg(self):
        return self.sanitize_for_msg({
            f"{attr}": self.__dict__[attr] for attr in dir(self) if not attr.startswith('__') and
                                                                    not callable(getattr(self, attr)) and
                                                                    self.__dict__[attr] is not None
        })

    def sanitize_for_msg(self, raw_values: dict) -> dict:
        sanitized_values = {}
        for key, value in raw_values.items():
            if isinstance(value, dict):
                sanitized_values |= {key: self.sanitize_for_msg(value)}
            elif value is not None:
                sanitized_values |= {key: value}

        return sanitized_values

    def unpack_for_debug(self):
        return {
            f"{attr}": self.__dict__[attr] for attr in dir(self) if not attr.startswith('__') and
                                                                    not callable(getattr(self, attr))
        }


class TableSafety(TableConfigParams):
    def __init__(self, ip: bool | None = None, gps: bool | None = None, disable_pc: bool | None = None,
                 email_restriction: bool | None = None, captcha: bool | None = None,
                 view_during_move: bool | None = None, **kwargs):
        super().__init__()
        self.ip = ip
        self.gps = gps
        self.disable_pc = disable_pc
        self.email_restriction = email_restriction
        self.captcha = captcha
        # TODO фактически отсутствует - бекэнд
        self.view_during_move = view_during_move

        logger.debug(f"table {self.cls_as_config_name()} initialized with {self.unpack_for_debug()}")

    @staticmethod
    def cls_as_config_name() -> str:
        return "safety_config"


class TableGameModesConfig(TableConfigParams):
    def __init__(self, game_type: str, game_subtype: str, jackpot: bool | None = None, ante_up: bool | None = None,
                 double_board: bool | None = None,
                 bomb_pot: bool | None = None, every_hand: int | None = None, bomb_pot_ante_min: int | None = None,
                 bomb_pot_ante_max: int | None = None, bomb_pot_triggers_double_board: bool | None = None,
                 seven_deuce: bool | None = None, each_prize: int | None = None, hi_low: bool | None = None,
                 ofc_joker: bool | None = None,
                 **kwargs):
        from ravvi_poker.engine.poker.plo import Poker_PLO_X
        from ravvi_poker.engine.poker.ofc import Poker_OFC_X, Poker_OFC_Limited

        super().__init__()
        self.jackpot = jackpot

        self.ante_up = ante_up

        self.double_board = double_board

        self.bombpot = bomb_pot
        if self.bombpot:
            self.bombpot = {
                "step": 1,
                "freq": every_hand,
                "ante_min": bomb_pot_ante_min,
                "ante_max": bomb_pot_ante_max,
                "double_board": bomb_pot_triggers_double_board
            }

        self.seven_deuce = seven_deuce
        self.each_prize = each_prize

        self.hi_low = None
        if game_type == Poker_PLO_X.GAME_TYPE:
            self.hi_low = hi_low

        self.ofc_joker = None
        if game_type == Poker_OFC_X.GAME_TYPE and game_subtype == Poker_OFC_Limited.GAME_SUBTYPE:
            self.ofc_joker = ofc_joker

        logger.debug(f"table {self.cls_as_config_name()} initialized with {self.unpack_for_debug()}")

    @staticmethod
    def cls_as_config_name() -> str:
        return "game_modes_config"


class TableRestrictionGameConfig(TableConfigParams):
    def __init__(self, vpip_level: int | None = None, hand_threshold: int | None = None, call_time: int | None = None,
                 call_time_type: str | None = None, **kwargs):
        super().__init__()
        self.vpip_level = vpip_level
        self.hand_threshold = hand_threshold
        self.call_time = call_time
        self.call_time_type = call_time_type

        logger.debug(f"table {self.cls_as_config_name()} initialized with {self.unpack_for_debug()}")

    @staticmethod
    def cls_as_config_name() -> str:
        return "restriction_game_config"


class TableRestrictionAccessConfig(TableConfigParams):
    def __init__(self, chat_mode: str | None = None, **kwargs):
        super().__init__()
        # TODO ожидается добавление
        self.chat_mode = None

    @staticmethod
    def cls_as_config_name() -> str:
        return "restriction_access_config"


class TableAdvancedConfig(TableConfigParams):
    def __init__(self, run_multi_times: int | None = None, ev_chop: bool | None = None, ratholing: int | None = None,
                 withdrawals: bool | None = None, **kwargs):
        super().__init__()
        # TODO фактически отсутсвуют - бекэнд
        self.run_multi_times = run_multi_times
        self.ev_chop = ev_chop
        self.ratholing = ratholing
        # TODO ожидается добавление
        self.chips_out = withdrawals

    @staticmethod
    def cls_as_config_name() -> str:
        return "advanced_config"


configCls = [
    TableSafety,
    TableGameModesConfig,
    TableRestrictionGameConfig,
    TableRestrictionAccessConfig,
    TableAdvancedConfig
]
