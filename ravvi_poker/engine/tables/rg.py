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

    def parse_props(self, buyin_min=100, buyin_max=None, blind_small: float = 0.01,
                    blind_big: float | None = None, ante_up: bool | None = None,
                    action_time=30, **kwargs):
        from ..poker.ante import AnteUpController
        from ..poker.bomb_pot import BombPotController
        from ..poker.seven_deuce import SevenDeuceController

        self.buyin_min = Decimal(buyin_min).quantize(Decimal("0.01"))
        self.buyin_max = Decimal(buyin_max).quantize(Decimal("0.01"))
        self.game_props.update(bet_timeout=action_time, blind_small=blind_small,
                               blind_big=blind_big if blind_big is not None else blind_small * 2)

        if ante_up:
            self.ante = AnteUpController(blind_small)
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

    async def on_player_enter(self, db: DBI, cmd_id, client_id, user, seat_idx):
        # lobby: get user_profile balance
        account = await db.get_account(user.account_id)
        if not account:
            return False
        # если не достаточно денег на балансе, то возвращаем ошибку
        if account.balance < self.buyin_min:
            msg = Message(msg_type=Message.Type.TABLE_WARNING,
                          table_id=self.table_id, cmd_id=cmd_id, client_id=client_id,
                          error_id=1, error_text='Not enough balance')
            await self.emit_msg(db, msg)
            return False
        # отправляем предложение выбрать buyin
        await self.make_player_offer(db, user, client_id, account.balance)
        # создаем сессию
        table_session = await db.register_table_session(table_id=self.table_id, account_id=account.id)
        user.table_session_id = table_session.id
        # ставим флаг, что это новый участник
        user.is_new_player_on_table = True
        self.log.info("on_player_enter(%s): done", user.id)
        return True

    async def make_player_offer(self, db, user: User, client_id: int, account_balance: decimal.Decimal):
        offer_closed_at = time.time() + 60
        buyin_min, buyin_max = self.buyin_min, self.buyin_max
        if user.balance is not None:
            if (buyin_min := self.buyin_min - user.balance) <= 0:
                buyin_min = self.game_props.get("blind_big")
            buyin_max -= user.balance
        elif user.balance is None and (interval_in_hours := getattr(self, "advanced_config").ratholing):
            # получаем последнюю выплату от стола за N часов
            buyin_min = buyin_max = await db.get_last_table_reward(self.table_id, user.account_id, interval_in_hours)
        # если пользователь ранее имел офферы, то разошлем сообщения, что они просрочены
        if user.buyin_offer_timeout:
            for client_id_expired_offer in user.clients:
                await self.emit_TABLE_JOIN_OFFER(db, client_id=client_id_expired_offer, offer_type="buyin",
                                                 table_id=self.table_id, balance=account_balance,
                                                 closed_at=0, buyin_min=buyin_min, buyin_max=buyin_max)
            await db.commit()
        # отправим действующий оффер
        await self.emit_TABLE_JOIN_OFFER(db, client_id=client_id, offer_type="buyin",
                                         table_id=self.table_id, balance=account_balance,
                                         closed_at=offer_closed_at, buyin_min=buyin_min, buyin_max=buyin_max)
        # стандартный оффер
        user.buyin_offer_timeout = offer_closed_at + 5

    async def handle_cmd_offer_result(self, db, *, cmd_id: int, client_id: int, user_id: int,
                                      buyin_cost: float | None):
        user, seat_idx, _ = self.find_user(user_id)
        if not user or seat_idx is None:
            return

        if buyin_cost is None:
            # пользователь запросил оффер - отправляем его
            account = await db.get_account(user.account_id)
            if not account:
                return

            await self.make_player_offer(db, user, client_id, account.balance)
        elif buyin_cost == 0:
            if user.buyin_offer_timeout is not None:
                # убираем у пользователя timeout timestamp оффера
                user.buyin_offer_timeout = None

                if user.balance is None:
                    # пользователь отклонил оффер - убираем его из-за стола
                    self.seats[seat_idx] = None
                    # оповещаем всех что пользователь вышел
                    await self.broadcast_PLAYER_EXIT(db, user.id)
                    # закрываем сессию если она была
                    if user.table_session_id:
                        await db.close_table_session(user.table_session_id)
                        user.table_session_id = None
        elif buyin_cost > 0:
            buyin_value = Decimal(buyin_cost).quantize(Decimal('.01'), rounding=ROUND_HALF_DOWN)
            # проверяем сумму buy-in
            account = await db.get_account(user.account_id)
            if not account:
                return
            if not await self.check_conditions_for_update_balance(db, cmd_id, client_id, account, user, buyin_value):
                return

            # если есть игра и пользователь в ней участвует, то моментальное пополнение не возможно
            if self.game:
                user.buyin_deferred_value = buyin_value
            else:
                # обновляем баланс
                user.buyin_offer_timeout = None
                await self.update_balance(db, user, buyin_value)

    async def on_player_exit(self, db: DBI, user, seat_idx):
        account = await db.get_account_for_update(user.account_id)
        if user.balance is not None:
            new_account_balance = account.balance + user.balance
            self.log.info("user %s exit %s -> balance %s", user.id, user.balance, new_account_balance)
            await db.create_account_txn(user.account_id, "CASHOUT", user.balance, sender_id=self.table_id,
                                        table_id=self.table_id)
            user.balance = None
        if user.table_session_id:
            await db.close_table_session(user.table_session_id)
            user.table_session_id = None
        self.log.info("on_player_exit(%s): done", user.id)

    async def run_buyin_timeout(self):
        while True:
            await self.sleep(1)
            async with (self.lock):
                for _, user in self.users.items():
                    # если пользователь имел оффер, он просрочен и баланс отсутствует, то убираем его из-за стола
                    if user.buyin_offer_timeout is not None \
                            and user.buyin_offer_timeout < time.time() and user.balance is None:
                        user.buyin_offer_timeout = None
                        async with DBI() as db:
                            user, seat_idx, _ = self.find_user(user.id)
                            if not user or seat_idx is None:
                                continue
                            # пользователь отклонил оффер - убираем его из-за стола
                            self.seats[seat_idx] = None
                            # оповещаем всех что пользователь вышел
                            await self.broadcast_PLAYER_EXIT(db, user.id)
                            # закрываем сессию если она была
                            if user.table_session_id:
                                await db.close_table_session(user.table_session_id)
                                user.table_session_id = None

    async def check_conditions_for_update_balance(self, db, cmd_id: int, client_id: int, account: Row, user: User,
                                                  buyin_value: Decimal) -> bool:
        # если не достаточно денег на балансе, то возвращаем ошибку
        if account.balance < buyin_value:
            msg = Message(msg_type=Message.Type.TABLE_WARNING,
                          table_id=self.table_id, cmd_id=cmd_id, client_id=client_id,
                          error_id=1, error_text='Not enough balance')
            await self.emit_msg(db, msg)
            return False

        # если баланс игрока уже больше максимального значения байина, то возвращаем ошибку
        if user.balance and user.balance >= self.buyin_max:
            msg = Message(msg_type=Message.Type.TABLE_WARNING, table_id=self.table_id, cmd_id=cmd_id,
                          client_id=client_id,
                          error_id=3, error_text='The maximum balance value has been exceeded')
            await self.emit_msg(db, msg)
            return False

        # если выбрана неверная сумма байина
        # проверим на рэтхолинг
        if user.balance is None and (interval_in_hours := getattr(self, "advanced_config").ratholing):
            if buyin_value != await db.get_last_table_reward(self.table_id, user.account_id, interval_in_hours):
                msg = Message(msg_type=Message.Type.TABLE_WARNING, table_id=self.table_id, cmd_id=cmd_id,
                              client_id=client_id,
                              error_id=2, error_text='Incorrect buyin value')
                await self.emit_msg(db, msg)
                return False
        # проверка при входе
        elif user.balance is None and not self.buyin_min <= buyin_value <= self.buyin_max:
            msg = Message(msg_type=Message.Type.TABLE_WARNING, table_id=self.table_id, cmd_id=cmd_id,
                          client_id=client_id,
                          error_id=2, error_text='Incorrect buyin value')
            await self.emit_msg(db, msg)
            return False
        # пополнение
        elif (user.balance is not None and not self.game_props.get("blind_big") <= buyin_value <=
                                               self.buyin_max - user.balance):
            msg = Message(msg_type=Message.Type.TABLE_WARNING, table_id=self.table_id, cmd_id=cmd_id,
                          client_id=client_id,
                          error_id=2, error_text='Incorrect buyin value')
            await self.emit_msg(db, msg)
            return False

        return True

    async def update_balance(self, db, user: User, buyin_value: Decimal):
        if user.balance is None:
            user.balance = buyin_value
        else:
            user.balance += buyin_value

        await db.create_account_txn(user.account_id, "BUYIN", -buyin_value, sender_id=None,
                                    table_id=self.table_id)

        # обновляем баланс
        await self.broadcast_PLAYER_BALANCE(db, user.id, user.balance)

    async def run_table(self):
        self.log.info("%s", self.status)

        # задача проверки buyin
        buyin_task = asyncio.create_task(self.run_buyin_timeout())

        # основной цикл
        while self.status == TableStatus.OPEN:
            await self.sleep(self.NEW_GAME_DELAY)
            # self.log.info("try start game")
            await self.run_game()
            async with self.lock:
                # пополним балансы пользователей, которые ранее это запросили
                async with self.DBI() as db:
                    for _, user in self.users.items():
                        if user.buyin_deferred_value:
                            account = await db.get_account_for_update(user.account_id)
                            if not (account.balance < user.buyin_deferred_value and
                                    user.balance + user.buyin_deferred_value > self.buyin_max):
                                await self.update_balance(db, user, user.buyin_deferred_value)
                            user.buyin_deferred_value = None
                async with self.DBI() as db:
                    await self.remove_users(db)

        # останавливаем задачу проверки buyin
        if not buyin_task.done():
            buyin_task.cancel()
