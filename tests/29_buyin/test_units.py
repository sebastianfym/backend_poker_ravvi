import time
from decimal import Decimal
from unittest.mock import MagicMock, AsyncMock

import pytest

from ravvi_poker.engine.tables.rg import Table_RG


class TestOfferResult:
    @pytest.mark.asyncio
    async def test_get_offer(self):
        """
        Проверяет, что если в значении buyin_value было передано None, то в ответ будет вызвана функция
        make_player_offer
        """
        table = Table_RG(1, "1", table_seats=2, props={"buyin_max": 10})
        user_mocked = MagicMock()
        user_mocked.account_id = 1
        table.find_user = MagicMock(return_value=(user_mocked, 1, None))
        make_player_offer = AsyncMock()
        table.make_player_offer = make_player_offer

        db_mocked = AsyncMock()
        account_mock = MagicMock()
        account_mock.balance = 10
        db_mocked.get_account.return_value = account_mock
        await table.handle_cmd_offer_result(db_mocked, cmd_id=1, client_id=1, user_id=1, buyin_cost=None)

        make_player_offer.assert_called_once_with(db_mocked, user_mocked, 1, 10)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("buyin_offer_timeout", [time.time(), None])
    async def test_decline_offer_case1(self, buyin_offer_timeout):
        """
        Проверяет, что если
            * в значении buyin_value было передано 0
            * user.buyin_offer_timeout is not None or None
            * user.balance is not None
        то в ничего не произойдет
        """
        table = Table_RG(1, "1", table_seats=2, props={"buyin_max": 10})
        user_mocked = MagicMock()
        user_mocked.buyin_offer_timeout = buyin_offer_timeout
        table.find_user = MagicMock(return_value=(user_mocked, 1, None))

        db_mocked = MagicMock()
        await table.handle_cmd_offer_result(db_mocked, cmd_id=1, client_id=1, user_id=1, buyin_cost=0)

        assert db_mocked.mock_calls == []

    @pytest.mark.asyncio
    async def test_decline_offer_case2(self):
        """
        Проверяет, что если
            * в значении buyin_value было передано 0
            * user.buyin_offer_timeout is not None
            * user.balance is None
        то пользователя высадит из-за стола, а сессия завершится
        """
        table = Table_RG(1, "1", table_seats=2, props={"buyin_max": 10})
        user_mocked = MagicMock()
        user_mocked.id = 105
        user_mocked.buyin_offer_timeout = time.time()
        user_mocked.balance = None
        user_mocked.table_session_id = 95
        table.find_user = MagicMock(return_value=(user_mocked, 1, None))
        broadcast_mock = AsyncMock()
        table.broadcast_PLAYER_EXIT = broadcast_mock

        db_mocked = AsyncMock()
        close_table_session_mocked = AsyncMock()
        db_mocked.close_table_session = close_table_session_mocked
        account_mock = MagicMock()
        account_mock.balance = 10
        db_mocked.get_account_for_update.return_value = account_mock
        await table.handle_cmd_offer_result(db_mocked, cmd_id=1, client_id=1, user_id=1, buyin_cost=0)

        broadcast_mock.assert_awaited_once_with(db_mocked, 105)
        close_table_session_mocked.assert_awaited_once_with(95)
        assert user_mocked.table_session_id is None

    @pytest.mark.asyncio
    async def test_accept_offer_case1(self):
        """
        Проверяет, что если все условия по buyin_value пройдены и нет активной игры, то сразу обновит баланс
        """
        table = Table_RG(1, "1", table_seats=2, props={"buyin_max": 10})
        user_mocked = MagicMock()
        user_mocked.account_id = 1
        table.find_user = MagicMock(return_value=(user_mocked, 1, None))
        table.check_conditions_for_update_balance = AsyncMock()
        update_balance_mock = AsyncMock()
        table.update_balance = update_balance_mock

        db_mocked = AsyncMock()
        account_mock = MagicMock()
        account_mock.balance = 10
        db_mocked.get_account_for_update.return_value = account_mock
        await table.handle_cmd_offer_result(db_mocked, cmd_id=1, client_id=1, user_id=1, buyin_cost=10.557)

        assert user_mocked.buyin_offer_timeout is None
        update_balance_mock.assert_awaited_once_with(db_mocked, user_mocked, Decimal("10.56"))


    @pytest.mark.asyncio
    async def test_accept_offer_case2(self):
        """
        Проверяет, что если все условия по buyin_value пройдены и есть активная игра, то запись баланс будет отложена
        """
        table = Table_RG(1, "1", table_seats=2, props={"buyin_max": 10})
        user_mocked = MagicMock()
        user_mocked.account_id = 1
        table.find_user = MagicMock(return_value=(user_mocked, 1, None))
        table.check_conditions_for_update_balance = AsyncMock()
        table.game = MagicMock()

        db_mocked = AsyncMock()
        account_mock = MagicMock()
        account_mock.balance = 10
        db_mocked.get_account_for_update.return_value = account_mock
        await table.handle_cmd_offer_result(db_mocked, cmd_id=1, client_id=1, user_id=1, buyin_cost=10.557)

        assert user_mocked.buyin_deferred_value == Decimal("10.56")
