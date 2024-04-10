import asyncio
import time

from psycopg.rows import Row

from .rg import Table_RG
from ..user import User
from ...db import DBI


class Table_RG_Club(Table_RG):

    async def user_can_stay(self, user: User):
        if user.inactive:
            return False
        if user.balance == 0 and user.buyin_deferred is None:
            user.balance = None
            async with DBI() as db:
                await self.broadcast_PLAYER_BALANCE(db, user.id, user.balance)
            # TODO вытянуть клиент который последний делал действия(Bet, take_seat), если количество клиентов
            #  больше одного
            client_id = list(user.clients)[0]
            async with DBI() as db:
                if not (account := await self.prepare_before_offer(db, None, client_id, user)):
                    return False
                await self.make_player_offer(db, user, client_id, account.balance)
            return True
        return self.user_can_play(user)

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

        await super().on_table_continue()
