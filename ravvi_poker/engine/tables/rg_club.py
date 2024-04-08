import asyncio
import decimal
import time
from decimal import Decimal, ROUND_HALF_DOWN
from psycopg.rows import Row

from ..user import User
from ...db import DBI
from .rg import Table_RG

class Table_RG_Club(Table_RG):

    async def on_player_enter(self, db: DBI, cmd_id, client_id, user: User, seat_idx):
        # lobby: get user_profile balance
        if not (account := await self.prepare_before_offer(db, cmd_id, client_id, user)):
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

    async def prepare_before_offer(self, db: DBI, cmd_id, client_id, user: User) -> Row | None:
        account = await db.get_account(user.account_id)
        if not account:
            return None
        # если не достаточно денег на балансе, то возвращаем ошибку
        if account.balance < self.buyin_min:
            await self.emit_TABLE_WARNING(db, cmd_id=cmd_id, client_id=client_id,
                          error_code=1, error_text='Not enough balance')
            return None
        return account

    async def make_player_offer(self, db, user: User, client_id: int, account_balance: decimal.Decimal):
        # игрок ранее не запрашивал оффер за этот стол
        if user.buyin_offer_timeout is None:
            offer_closed_at = time.time() + 60
        # игрок уже имеет активный оффер
        else:
            # TODO обработать отрицательное значение относительно текущего времени
            offer_closed_at = user.buyin_offer_timeout - 5
        buyin_min, buyin_max = self.buyin_min, self.buyin_max
        # если денег на балансе уже больше максимального байина, то возвращаем ошибку
        if user.balance is not None and user.balance >= buyin_max:
            await self.emit_TABLE_WARNING(db, cmd_id=None,
                          client_id=client_id,
                          error_code=3, error_text='The maximum balance value has been exceeded')
            return
        # если недостаточно денег на балансе до минимального байина, то возвращаем ошибку
        if buyin_min > account_balance:
            await self.emit_TABLE_WARNING(db, cmd_id=None, client_id=client_id,
                          error_code=1, error_text='Not enough balance')
            return
        # если максимальный байин больше чем денег на балансе, то максимальный байин равен балансу
        if buyin_max > account_balance:
            buyin_max = account_balance
        # иначе вычитаем тот баланс что уже есть
        elif user.balance is not None:
            buyin_max -= user.balance
        if user.balance is not None:
            buyin_min -= user.balance
            if buyin_min < 0:
                buyin_min = min(self.game_props.get("blind_big"), buyin_max)
        elif user.balance is None and (interval_in_hours := getattr(self, "advanced_config").ratholing):
            # получаем последнюю выплату от стола за N часов
            # TODO дополнить правило рэтхолинга, если последняя выплата равна байину, то рэтхолинга нет
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
                                         closed_at=int(offer_closed_at - time.time()),
                                         buyin_min=buyin_min, buyin_max=buyin_max)
        if user.buyin_offer_timeout is None:
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

            # TODO проверить что пользователь в игре
            # если есть игра и пользователь в ней участвует, то моментальное пополнение не возможно
            if self.game:
                user.buyin_deferred = buyin_value
            else:
                # обновляем баланс
                user.buyin_offer_timeout = None
                await self.update_balance(db, user, buyin_value)

    async def on_player_exit(self, db: DBI, user, seat_idx):
        account = await db.get_account_for_update(user.account_id)
        if user.balance is not None:
            new_account_balance = account.balance + user.balance
            self.log.info("user %s exit %s -> balance %s", user.id, user.balance, new_account_balance)
            await db.create_account_txn(user.account_id, "REWARD", user.balance, sender_id=self.table_id,
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
            await self.emit_TABLE_WARNING(db, cmd_id=cmd_id, client_id=client_id,
                          error_code=1, error_text='Not enough balance')
            return False

        # если баланс игрока уже больше максимального значения байина, то возвращаем ошибку
        if user.balance and user.balance >= self.buyin_max:
            await self.emit_TABLE_WARNING(db, cmd_id=cmd_id,
                          client_id=client_id,
                          error_code=3, error_text='The maximum balance value has been exceeded')
            return False

        # если выбрана неверная сумма байина
        # проверим на рэтхолинг
        if user.balance is None and (interval_in_hours := getattr(self, "advanced_config").ratholing):
            if buyin_value != await db.get_last_table_reward(self.table_id, user.account_id, interval_in_hours):
                await self.emit_TABLE_WARNING(db, cmd_id=cmd_id,
                              client_id=client_id,
                              error_code=2, error_text='Incorrect buyin value')
                return False
        # проверка при входе
        elif user.balance is None and not self.buyin_min <= buyin_value <= self.buyin_max:
            await self.emit_msg(db, cmd_id=cmd_id,
                          client_id=client_id,
                          error_code=2, error_text='Incorrect buyin value')
            return False
        # пополнение
        elif (user.balance is not None and not self.buyin_min - user.balance <= buyin_value <=
                                               self.buyin_max - user.balance):
            await self.emit_TABLE_WARNING(db, cmd_id=cmd_id,
                          client_id=client_id,
                          error_code=2, error_text='Incorrect buyin value')
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

    async def on_table_prepare(self):
        # задача проверки buyin
        self.task_secondary = asyncio.create_task(self.run_buyin_timeout())
        return True
        
    async def on_table_continue(self):
        # пополним балансы пользователей, которые ранее это запросили
        async with self.DBI() as db:
            for _, user in self.users.items():
                if user.buyin_deferred:
                    account = await db.get_account_for_update(user.account_id)
                    if (account.balance >= user.buyin_deferred and
                            user.balance + user.buyin_deferred <= self.buyin_max):
                        await self.update_balance(db, user, user.buyin_deferred)
                    user.buyin_deferred = None
        
        super().on_table_continue()
