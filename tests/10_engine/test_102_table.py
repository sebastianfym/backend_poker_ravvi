import pytest
from ravvi_poker.engine.table import Table, User
from ravvi_poker.engine.game import Game

# see X_DBI & X_Table at the end of file

def test_102_1_table_info():
    table = X_Table(1)
    info = table.get_table_info(777)

    assert info['table_id'] == 1

@pytest.mark.asyncio
async def test_102_2_user_lifecycle():
    TABLE_ID = 777
    USER_ID = 666
    TABLE_INFO_EVENT_TYPE = 101
    PLAYER_ENTER_EVENT_TYPE = 201
    PLAYER_SEAT_EVENT_TYPE = 202
    PLAYER_EXIT_EVENT_TYPE = 299

    db = X_DBI()
    table = X_Table(TABLE_ID)
    assert not table.users

    # ПОЛЬЗОВАТЕЛЬ НЕ СИДИТ ЗА СТОЛОМ
    user, seat_idx, seats_available = table.find_user(1)
    assert user is None and seat_idx is None
    assert seats_available == [0,1,2,3,4,5,6,7,8]

    # подключаемся без места (посадка запрещена)
    table._user_enter_enabled = False
    async with db:
        await table.handle_cmd_join(db, user_id=USER_ID, client_id=100, take_seat=False)
    # подтверждение подключения
    assert len(db._events) == 1
    assert db._event.table_id == TABLE_ID
    assert db._event.type == TABLE_INFO_EVENT_TYPE
    assert db._event.client_id==100

    user, seat_idx, _ = table.find_user(USER_ID)
    assert user and user.id == USER_ID
    assert user.balance is None
    assert user.connected
    assert user.clients == {100}
    assert seat_idx is None
    assert all(s is None for s in table.seats)

    # c запросом места (посадка запрещена)
    table._user_enter_enabled = False
    async with db:
        await table.handle_cmd_join(db, user_id=USER_ID, client_id=101, take_seat=True)
    # подтверждение подключения
    assert len(db._events) == 1
    assert db._event.table_id == TABLE_ID
    assert db._event.type == TABLE_INFO_EVENT_TYPE
    assert db._event.client_id==101

    user, seat_idx, _ = table.find_user(USER_ID)
    assert user and user.id == USER_ID
    assert user.balance is None
    assert user.connected
    assert user.clients == {100, 101}
    assert seat_idx is None
    assert all(s is None for s in table.seats)

    # без места (посадка разрешена)
    table._user_enter_enabled = True
    async with db:
        await table.handle_cmd_join(db, user_id=USER_ID, client_id=110, take_seat=False)
    # подтверждение подключения
    assert len(db._events) == 1
    assert db._event.table_id == TABLE_ID
    assert db._event.type == TABLE_INFO_EVENT_TYPE
    assert db._event.client_id==110

    user, seat_idx, _ = table.find_user(USER_ID)
    assert user and user.id == USER_ID
    assert user.balance is None
    assert user.connected
    assert user.clients == {100, 101, 110}
    assert seat_idx is None
    assert all(s is None for s in table.seats)

    # садимся на место 3
    async with db:
        await table.handle_cmd_take_seat(db, user_id=USER_ID, seat_idx=3)
    # подтверждение
    assert len(db._events) == 1
    assert db._event.table_id == TABLE_ID
    assert db._event.type == PLAYER_ENTER_EVENT_TYPE

    # сел на место 3
    user, seat_idx, _ = table.find_user(USER_ID)
    assert user and user.id == USER_ID
    assert user.balance == 1
    assert user.connected
    assert user.clients == {100, 101, 110}
    assert seat_idx == 3
    assert table.seats[seat_idx] == user
    assert all(s is None for i, s in enumerate(table.seats) if i!=seat_idx)

    # садимся на место (invalid user)
    async with db:
        await table.handle_cmd_take_seat(db, user_id=123456, seat_idx=7)
    # подтверждение
    assert not db._events

    # садимся на место (invalid seat_idx)
    async with db:
        await table.handle_cmd_take_seat(db, user_id=USER_ID, seat_idx=123456)
    # подтверждение
    assert not db._events

    # садимся на место 7
    async with db:
        await table.handle_cmd_take_seat(db, user_id=USER_ID, seat_idx=7)
    # подтверждение
    assert len(db._events) == 1
    assert db._event.table_id == TABLE_ID
    assert db._event.type == PLAYER_SEAT_EVENT_TYPE

    # сел на место 7
    user, seat_idx, _ = table.find_user(USER_ID)
    assert user and user.id == USER_ID
    assert user.balance == 1
    assert user.connected
    assert user.clients == {100, 101, 110}
    assert seat_idx == 7
    assert table.seats[seat_idx] == user
    assert all(s is None for i, s in enumerate(table.seats) if i!=seat_idx)

    # выходим со стола (выход запрещен)
    table._user_exit_enabled = False
    async with db:
        await  table.handle_cmd_exit(db, user_id=USER_ID, client_id=None)
    assert not db._events

    assert user and user.id == USER_ID
    assert user.balance == 1
    assert user.connected
    assert user.clients == {100, 101, 110}
    assert seat_idx == 7
    assert table.seats[seat_idx] == user
    assert all(s is None for i, s in enumerate(table.seats) if i!=seat_idx)

    # выходим со стола (выход разрешен)
    table._user_exit_enabled = True
    async with db:
        await  table.handle_cmd_exit(db, user_id=USER_ID, client_id=None)
    assert len(db._events) == 1
    assert db._event.table_id == TABLE_ID
    assert db._event.type == PLAYER_EXIT_EVENT_TYPE

    user, seat_idx, _ = table.find_user(USER_ID)
    assert user and user.id == USER_ID
    assert user.balance == 0
    assert user.connected
    assert user.clients == {100, 101, 110}
    assert seat_idx is None
    assert all(s is None for s in table.seats)

    # выходим со стола (invalid user)
    table._user_exit_enabled = True
    async with db:
        await  table.handle_cmd_exit(db, user_id=123456)
    assert not db._events

    # c запросом места (посадка разрешена)
    table._user_enter_enabled = True
    async with db:
        await table.handle_cmd_join(db, user_id=USER_ID, client_id=111, take_seat=True)
    # подтверждение подключения
    assert len(db._events) == 2
    e201 = db._events[0]
    assert e201.table_id == TABLE_ID
    assert e201.type == PLAYER_ENTER_EVENT_TYPE
    assert e201.client_id is None
    e101 = db._events[1]
    assert e101.table_id == TABLE_ID
    assert e101.type == TABLE_INFO_EVENT_TYPE
    assert e101.client_id==111

    # сел на место 0
    user, seat_idx, _ = table.find_user(USER_ID)
    assert user and user.id == USER_ID
    assert user.balance == 1
    assert user.connected
    assert user.clients == {100, 101, 110, 111}
    assert seat_idx == 0
    assert table.seats[seat_idx] == user
    assert all(s is None for i, s in enumerate(table.seats) if i!=seat_idx)

    # ПОЛЬЗОВАТЕЛЬ УЖЕ ЗА СТОЛОМ

    # подключаемся без места (посадка запрещена)
    table._user_enter_enabled = False
    async with db:
        await table.handle_cmd_join(db, user_id=USER_ID, client_id=200, take_seat=False)
    # подтверждение подключения
    assert len(db._events) == 1
    assert db._event.table_id == TABLE_ID
    assert db._event.type == TABLE_INFO_EVENT_TYPE
    assert db._event.client_id==200
    
    user, seat_idx, _ = table.find_user(USER_ID)
    assert user and user.id == USER_ID
    assert user.balance == 1
    assert user.connected
    assert user.clients == {100, 101, 110, 111, 200}
    assert seat_idx == 0
    assert table.seats[seat_idx] == user
    assert all(s is None for i, s in enumerate(table.seats) if i!=seat_idx)

    # c запросом места (посадка запрещена)
    table._user_enter_enabled = False
    async with db:
        await table.handle_cmd_join(db, user_id=USER_ID, client_id=201, take_seat=True)
    # подтверждение подключения
    assert len(db._events) == 1
    assert db._event.table_id == TABLE_ID
    assert db._event.type == TABLE_INFO_EVENT_TYPE
    assert db._event.client_id==201

    user, seat_idx, _ = table.find_user(USER_ID)
    assert user and user.id == USER_ID
    assert user.balance == 1
    assert user.connected
    assert user.clients == {100, 101, 110, 111, 200, 201}
    assert seat_idx == 0
    assert table.seats[seat_idx] == user
    assert all(s is None for i, s in enumerate(table.seats) if i!=seat_idx)

    # без места (посадка разрешена)
    table._user_enter_enabled = True
    async with db:
        await table.handle_cmd_join(db, user_id=USER_ID, client_id=210, take_seat=False)
    # подтверждение подключения
    assert len(db._events) == 1
    assert db._event.table_id == TABLE_ID
    assert db._event.type == TABLE_INFO_EVENT_TYPE
    assert db._event.client_id==210

    user, seat_idx, _ = table.find_user(USER_ID)
    assert user and user.id == USER_ID
    assert user.balance == 1
    assert user.connected
    assert user.clients == {100, 101, 110, 111, 200, 201, 210}
    assert seat_idx == 0
    assert table.seats[seat_idx] == user
    assert all(s is None for i, s in enumerate(table.seats) if i!=seat_idx)

    # c запросом места (посадка разрешена)
    table._user_enter_enabled = True
    async with db:
        await table.handle_cmd_join(db, user_id=USER_ID, client_id=211, take_seat=True)
    # подтверждение подключения
    assert len(db._events) == 1
    assert db._event.table_id == TABLE_ID
    assert db._event.type == TABLE_INFO_EVENT_TYPE
    assert db._event.client_id==211

    user, seat_idx, _ = table.find_user(USER_ID)
    assert user and user.id == USER_ID
    assert user.balance == 1
    assert user.connected
    assert user.clients == {100, 101, 110, 111, 200, 201, 210, 211}
    assert seat_idx == 0
    assert table.seats[seat_idx] == user
    assert all(s is None for i, s in enumerate(table.seats) if i!=seat_idx)

    # ОТКЛЮЧАЕМ КЛИЕНТОВ кроме 2х (210, 211) - все клиенты равнозначны
    clients = sorted(user.clients)[:-2]
    for client_id in clients:
        async with db:
            await  table.handle_client_close(db, user_id=USER_ID, client_id=client_id)
        assert not db._events
        user, seat_idx, _ = table.find_user(USER_ID)
        assert user and user.id == USER_ID
        assert user.balance == 1
        assert user.connected
        assert client_id not in user.clients
        assert seat_idx == 0
        assert table.seats[seat_idx] == user
        assert all(s is None for i, s in enumerate(table.seats) if i!=seat_idx)
    assert user.clients == {210, 211}

    # выходим со стола
    async with db:
        await  table.handle_cmd_exit(db, user_id=USER_ID, client_id=210)
    assert len(db._events) == 1
    assert db._event.table_id == TABLE_ID
    assert db._event.type == 299

    user, seat_idx, _ = table.find_user(USER_ID)
    assert user and user.id == USER_ID
    assert user.balance == 0
    assert user.connected
    assert user.clients == {210, 211}
    assert seat_idx is None
    assert all(s is None for s in table.seats)

    # invalid client
    async with db:
        await  table.handle_client_close(db, user_id=USER_ID, client_id=123456)
    assert not db._events

    # ОТКЛЮЧАЕМ КЛИЕНТОВ 210, 211
    async with db:
        await  table.handle_client_close(db, user_id=USER_ID, client_id=210)
    assert not db._events
    user, seat_idx, _ = table.find_user(USER_ID)
    assert user and user.id == USER_ID
    assert user.balance == 0
    assert user.connected
    assert user.clients == {211}
    assert seat_idx is None
    assert all(s is None for s in table.seats)

    async with db:
        await  table.handle_client_close(db, user_id=USER_ID, client_id=211)
    assert not db._events
    user, seat_idx, _ = table.find_user(USER_ID)
    assert user is None
    assert seat_idx is None
    assert all(s is None for s in table.seats)

@pytest.mark.asyncio
async def test_102_9_run_all_together():
    TABLE_ID = 777
    X_DBI._events_keep = True
    db = X_DBI()
    table = X_Table(TABLE_ID)

    await table.start()
    await asyncio.sleep(1)
    async with db:
        await table.handle_cmd_join(db, user_id=111, client_id=111, take_seat=True)
    await asyncio.sleep(1)
    async with db:
        await table.handle_cmd_join(db, user_id=222, client_id=222, take_seat=True)
    while X_DBI._game_id<3:
        await asyncio.sleep(1)
    await table.stop()

    db._print_events()

from collections import namedtuple

class X_DBI:
    _game_id = 1
    _events = list()
    _events_keep = False
    
    GameRow = namedtuple('GameRow', ['id'])

    def __init__(self) -> None:
        pass

    async def __aenter__(self):
        if not X_DBI._events_keep:
            X_DBI._events = []
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        pass
    
    async def emit_event(self, event):
        logging.info("db_event: %s", event)
        X_DBI._events.append(event)

    async def game_begin(self, *, table_id, users, game_type, game_subtype, game_props):
        X_DBI._game_id += 1
        return X_DBI.GameRow(X_DBI._game_id)

    async def game_close(self, game_id, users):
        pass

    @property
    def _event(self):
        return X_DBI._events[-1] if X_DBI._events else None

    def _print_events(self):
        for x in X_DBI._events:
            print(x)

class X_Game(Game):
    DBI = X_DBI
    GAME_TYPE = 'X_GT'
    GAME_SUBTYPE = 'X_GST'

    def __init__(self, table, users) -> None:
        super().__init__(table, users)

    async def run(self):
        async with self.table.lock:
            async with self.DBI() as db:
                await self.broadcast_GAME_BEGIN(db)
        await asyncio.sleep(3)
        async with self.table.lock:
            async with self.DBI() as db:
                await self.broadcast_GAME_END(db)


class X_Table(Table):
    DBI = X_DBI
    TABLE_TYPE = 'X'

    def __init__(self, id):
        super().__init__(id, table_seats=9)
        self._user_enter_enabled = True
        self._user_exit_enabled = True

    @property
    def user_enter_enabled(self):
        return self._user_enter_enabled

    @property
    def user_exit_enabled(self):
        return self._user_exit_enabled

    async def user_factory(self, db, user_id):
        user = self.users.get(user_id, None)
        if not user:
            username='u'+str(user_id)
            user = User(id=user_id, username=username)
            self.users[user_id] = user
        return user
    
    async def game_factory(self, users):
        return X_Game(self, users)


if __name__=='__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    import asyncio
    asyncio.run(test_102_2_user_lifecycle())
    asyncio.run(test_102_9_run_all_together())
    #asyncio.run(test_102_3_user_move_seat())