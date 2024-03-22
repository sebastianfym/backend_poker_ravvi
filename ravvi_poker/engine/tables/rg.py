import asyncio
import decimal
import time

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

        self.buyin_min = buyin_min
        self.buyin_max = buyin_max
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
        # TODO убрать FOR UPDATE
        account = await db.get_account_for_update(user.account_id)
        if not account:
            return False
        # если не достаточно денег на балансе, то возвращаем ошибку
        if account.balance < self.buyin_min:
            msg = Message(msg_type=Message.Type.TABLE_ERROR, table_id=self.table_id, cmd_id=cmd_id, client_id=client_id,
                          error_id=400, error_text='Not enough balance')
            await self.emit_msg(db, msg)
            return False
        # отправляем предложение выбрать buyin
        await self.make_player_offer(db, user, client_id, account.balance)
        # создаем сессию
        table_session = await db.register_table_session(table_id=self.table_id, account_id=account.id)
        user.table_session_id = table_session.id
        # buyin = self.buyin_min
        # TODO: точность и округление
        # new_account_balance = float(account.balance) - buyin
        # self.log.info("user %s buyin %s -> balance %s", user.id, buyin, new_account_balance)
        # await db.create_account_txn(user.account_id, "BUYIN", -buyin, sender_id=None, table_id=self.table_id)
        # user.balance = buyin
        self.log.info("on_player_enter(%s): done", user.id)
        return True

    async def make_player_offer(self, db, user: User, client_id: int, account_balance: decimal.Decimal):
        offer_closed_at = time.time() + 60
        # TODO временно только range (нужна реализация ratholing)
        buyin_range = [self.buyin_min, self.buyin_max]
        if user.balance is not None:
            buyin_range = [self.buyin_min - user.balance
                           if self.buyin_min - user.balance > 0 else self.game_props.get("blind_big"),
                           self.buyin_max - user.balance]
        await self.emit_TABLE_JOIN_OFFER(db, client_id=client_id, offer_type="buyin",
                                         table_id=self.table_id, balance=account_balance,
                                         closed_at=offer_closed_at, buyin_range=buyin_range)
        # TODO пользователь может попытаться сесть за один стол несколько раз подряд
        user.buyin_offer_timeout = offer_closed_at + 5

    async def handle_cmd_offer_result(self, db, *, cmd_id: int, client_id: int, user_id: int,
                                      buyin_value: float | None):
        user, seat_idx, _ = self.find_user(user_id)
        if not user or seat_idx is None:
            return

        if buyin_value is None:
            # пользователь запросил оффер - отправляем его
            # TODO убрать FOR UPDATE
            account = await db.get_account_for_update(user.account_id)
            if not account:
                return

            await self.make_player_offer(db, user, client_id, account.balance)
        elif buyin_value == 0:
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
        elif buyin_value > 0:
            # TODO ratholing
            # TODO использовать Decimal
            # если есть игра и пользователь в ней участвует и не находится в состоянии FOLD то моментальное
            # пополнение не возможно
            if self.game:
                pass
                # TODO создаем задачу пополнить
            else:
                # пользователь выбрал сумму бай-ин, если она верная, то обновляем его баланс
                # проверяем сумму buy-in
                account = await db.get_account_for_update(user.account_id)
                if not account:
                    return
                # если не достаточно денег на балансе, то возвращаем ошибку
                if account.balance < buyin_value:
                    msg = Message(msg_type=Message.Type.TABLE_ERROR, table_id=self.table_id, cmd_id=cmd_id,
                                  client_id=client_id,
                                  error_id=400, error_text='Not enough balance')
                    await self.emit_msg(db, msg)
                    return
                # если баланс игрока уже больше максимального значения байина, то возвращаем ошибку
                if user.balance and user.balance >= self.buyin_max:
                    msg = Message(msg_type=Message.Type.TABLE_ERROR, table_id=self.table_id, cmd_id=cmd_id,
                                  client_id=client_id,
                                  error_id=400, error_text='The maximum balance value has been exceeded')
                    await self.emit_msg(db, msg)
                    return

                if (user.balance is None and
                    self.buyin_min <= buyin_value <= self.buyin_max) or \
                        (user.balance is not None and
                         self.game_props.get("blind_big") <= buyin_value <= self.buyin_max - user.balance):
                    user.buyin_offer_timeout = None
                    user.balance = buyin_value

                    await db.create_account_txn(user.account_id, "BUYIN", -buyin_value, sender_id=None,
                                                table_id=self.table_id)

                    # обновляем баланс
                    await self.broadcast_PLAYER_BALANCE(db, user_id, buyin_value)
                else:
                    msg = Message(msg_type=Message.Type.TABLE_ERROR, table_id=self.table_id, cmd_id=cmd_id,
                                  client_id=client_id,
                                  error_id=400, error_text='Incorrect buyin value')
                    await self.emit_msg(db, msg)
                    return

    async def on_player_exit(self, db: DBI, user, seat_idx):
        account = await db.get_account_for_update(user.account_id)
        if user.balance is not None:
            # TODO: точность и округление
            new_account_balance = float(account.balance) + user.balance
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
            await self.sleep(2)
            for _, user in self.users.items():
                # если пользователь имел оффер, он просрочен и баланс отсутствует, то убираем его из-за стола
                if user.buyin_offer_timeout and user.buyin_offer_timeout < time.time() and user.balance is None:
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
                # TODO просмотреть задачи на пополнения

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
                async with self.DBI() as db:
                    await self.remove_users(db)

        # останавливаем задачу проверки buyin
        if not buyin_task.done():
            buyin_task.cancel()
