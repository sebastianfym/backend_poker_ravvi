import pytest

from ravvi_poker.engine.poker.ante import AnteUpController
from ravvi_poker.engine.tables import Table_RG
from tests.helpers.x_table import X_Game


class TestAnteUpControllerInstance:
    TABLE_ID = 777
    TABLE_NAME = "test_table"

    @pytest.mark.asyncio
    async def test_ante_params_exist(self):
        """
            Проверяем что если настройка ante_up выставлена, то мы увидим инициализированный инстанс ante_up_controller
        """
        table = Table_RG(self.TABLE_ID, self.TABLE_NAME, table_seats=3,
                         props={
                             "ante_up": True
                         })

        assert isinstance(getattr(table, "ante"), AnteUpController)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("ante_up", [None, False])
    async def test_ante_params_not_exist(self, ante_up):
        """
            Проверяем что если настройка ante_up не выставлена или выставлена в False, то мы не увидим
            инициализированный инстанс ante_up_controller
        """
        table = Table_RG(self.TABLE_ID, self.TABLE_NAME, table_seats=3,
                         props={
                             "ante_up": False
                         })

        assert getattr(table, "ante") is None


def prepare_ante_by_blind() -> list:
    rule_base_cases = [
        {"blind_small_value": 0.02, "ante_target_value": 0.01},
        {"blind_small_value": 0.03, "ante_target_value": 0.01},
        {"blind_small_value": 0.04, "ante_target_value": 0.01},
    ]

    for blind_small_value in [0.05, 0.1, 0.2, 0.25, 0.3, 0.4, 0.5,
                              1, 2, 2.5, 3, 4, 5,
                              10, 15, 20, 25, 50,
                              100, 150, 200, 250, 300, 400, 500,
                              1000, 1500, 2000, 2500, 3000, 4000, 5000, 6000, 7000, 8000, 9000,
                              10000]:
        # TODO округление
        target_ante_value = round(blind_small_value * 2 * 0.2, 2)
        rule_base_cases.append({"blind_small_value": blind_small_value, "ante_target_value": target_ante_value})

    return rule_base_cases


def prepare_test_cases_for_games_with_possible_ante_up() -> list:
    # поддерживаемые типы игр
    cases_base = (
            [
                {"game_type": "NLH", "game_subtype": subtype} for subtype in ["REGULAR", "3-1"]
            ] + [
                {"game_type": "PLO", "game_subtype": subtype} for subtype in ["PLO4", "PLO5", "PLO6"]
            ])

    ante_by_blind_cases = prepare_ante_by_blind()

    result = []
    for case in cases_base:
        for ante_by_blind_case in ante_by_blind_cases:
            result.append(case | ante_by_blind_case)

    return result


def prepare_test_cases_for_games_without_possible_ante_up() -> list:
    # поддерживаемые типы игр
    cases_base = (
        [
            {"game_type": "NLH", "game_subtype": subtype} for subtype in ["AOF", "6+"]
        ])

    ante_by_blind_cases = prepare_ante_by_blind()

    result = []
    for case in cases_base:
        for ante_by_blind_case in ante_by_blind_cases:
            result.append(case | ante_by_blind_case | {"ante_target_value": None})

    return result


def pytest_generate_tests(metafunc):
    try:
        func_arg_list = metafunc.cls.params[metafunc.function.__name__]
        arg_names = sorted(func_arg_list[0])
        metafunc.parametrize(
            arg_names, [[func_args[name] for name in arg_names] for func_args in func_arg_list]
        )
    except AttributeError:
        pass


class TestAnteUpControllerInitialValueForGame:
    TABLE_ID = 777
    TABLE_NAME = "test_table"
    params = {
        "test_initial_ante_value_for_tables_with_possible_ante_up":
            prepare_test_cases_for_games_with_possible_ante_up(),
        "test_initial_ante_value_for_tables_without_possible_ante_up":
            prepare_test_cases_for_games_without_possible_ante_up(),
    }

    @pytest.mark.asyncio
    async def test_initial_ante_value_for_tables_with_possible_ante_up(self, game_type: str, game_subtype: str,
                                                                       blind_small_value: float,
                                                                       ante_target_value: float):
        """
            Проверяет что первое значение которое будет передано игре от стола верное
        """
        table = Table_RG(self.TABLE_ID, self.TABLE_NAME, table_seats=3, game_type=game_type, game_subtype=game_subtype,
                         props={
                             "ante_up": True,
                             "blind_small": blind_small_value
                         })
        game = await table.game_factory([])

        assert game.current_ante_value == ante_target_value

    @pytest.mark.asyncio
    @pytest.mark.parametrize("ante_up", [True, False, None])
    async def test_initial_ante_value_for_tables_without_possible_ante_up(self, game_type: str, game_subtype: str,
                                                                          blind_small_value: float,
                                                                          ante_target_value: float,
                                                                          ante_up: bool):
        """
            Проверяет что поведение current_ante_value будет верным для режимов не поддерживающих ante в
            независимости от параметров ante_up
        """
        table = Table_RG(self.TABLE_ID, self.TABLE_NAME, table_seats=3, game_type=game_type, game_subtype=game_subtype,
                         props={
                             "ante_up": ante_up,
                             "blind_small": blind_small_value
                         })
        game = await table.game_factory([])

        assert game.current_ante_value == ante_target_value


# class TestAnteInGame:
#     @pytest.mark.asyncio
#     async def test_case(self, game_case):
#         name, kwargs = game_case
#
#         game = X_Game(None, **kwargs)
#         await game.run()
#         assert not game._check_steps
