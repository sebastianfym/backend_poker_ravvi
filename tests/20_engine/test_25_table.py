import pytest
import asyncio

import logging
logger = logging.getLogger(__name__)

from ravvi_poker.db.dbi import DBI
from ravvi_poker.engine.user import User
from ravvi_poker.engine.events import Command, Message
from ravvi_poker.engine.table import Table
from ravvi_poker.engine.game import Game

from helpers.x_dbi import X_DBI
from helpers.x_table import X_Table, X_Game

@pytest.mark.dependency()
def test_x_classes():
   X_DBI.check_methods_compatibility()
   X_Table.check_methods_compatibility()
   X_Game.check_methods_compatibility()


@pytest.mark.dependency(depends=["test_x_classes"])
@pytest.mark.asyncio
async def test_user_lifecycle():
    TABLE_ID = 777
    USER_ID = 666
    TABLE_INFO_EVENT_TYPE = 101
    PLAYER_ENTER_EVENT_TYPE = 201
    PLAYER_SEAT_EVENT_TYPE = 202
    PLAYER_EXIT_EVENT_TYPE = 299
    BUYIN_VALUE = 1111111111

    db = X_DBI()
    table = X_Table(TABLE_ID, BUYIN_VALUE)
    assert not table.users

    # ПОЛЬЗОВАТЕЛЬ НЕ СИДИТ ЗА СТОЛОМ
    user, seat_idx, seats_available = table.find_user(1)
    assert user is None and seat_idx is None
    assert seats_available == [0,1,2,3,4,5,6,7,8]

    # подключаемся без места (посадка запрещена)
    table._user_enter_enabled = False
    async with db:
        await table.handle_cmd(db, cmd_id=11, user_id=USER_ID, client_id=100, cmd_type=Command.Type.JOIN, props=dict(take_seat=False))
    # подтверждение подключения
    assert len(db._events) == 1
    assert db._event.table_id == TABLE_ID
    assert db._event.msg_type == Message.Type(TABLE_INFO_EVENT_TYPE)
    assert db._event.client_id==100

    user, seat_idx, _ = table.find_user(USER_ID)
    assert user and user.id == USER_ID
    assert user.balance is None
    assert user.connected
    assert user.clients == {100}
    assert seat_idx is None
    assert all(s is None for s in table.seats)

    # садимся на место 3 (посадка запрещена)
    async with db:
        await table.handle_cmd(db, cmd_id=12, user_id=USER_ID, client_id=100, cmd_type=Command.Type.TAKE_SEAT, props=dict(seat_idx=3))
    # подтверждение
    assert not db._events
    
    # c запросом места (посадка запрещена)
    table._user_enter_enabled = False
    async with db:
        await table.handle_cmd(db, cmd_id=13, user_id=USER_ID, client_id=101, cmd_type=Command.Type.JOIN, props=dict(take_seat=True))
    # подтверждение подключения
    assert len(db._events) == 1
    assert db._event.table_id == TABLE_ID
    assert db._event.msg_type == Message.Type(TABLE_INFO_EVENT_TYPE)
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
        await table.handle_cmd(db, cmd_id=14, user_id=USER_ID, client_id=110, cmd_type=Command.Type.JOIN, props=dict(take_seat=False))
    # подтверждение подключения
    assert len(db._events) == 1
    assert db._event.table_id == TABLE_ID
    assert db._event.msg_type == Message.Type(TABLE_INFO_EVENT_TYPE)
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
        await table.handle_cmd(db, cmd_id=15, user_id=USER_ID, client_id=100, cmd_type=Command.Type.TAKE_SEAT, props=dict(seat_idx=3))
    # подтверждение
    assert len(db._events) == 1
    assert db._event.table_id == TABLE_ID
    assert db._event.msg_type == Message.Type(PLAYER_ENTER_EVENT_TYPE)

    # сел на место 3
    user, seat_idx, _ = table.find_user(USER_ID)
    assert user and user.id == USER_ID
    assert user.balance == BUYIN_VALUE
    assert user.connected
    assert user.clients == {100, 101, 110}
    assert seat_idx == 3
    assert table.seats[seat_idx] == user
    assert all(s is None for i, s in enumerate(table.seats) if i!=seat_idx)

    # садимся на место (invalid user)
    async with db:
        await table.handle_cmd(db, cmd_id=16, user_id=123456, client_id=100, cmd_type=Command.Type.TAKE_SEAT, props=dict(seat_idx=3))
    # подтверждение
    assert not db._events

    # садимся на место (invalid seat_idx)
    async with db:
        await table.handle_cmd(db, cmd_id=17, user_id=USER_ID, client_id=100, cmd_type=Command.Type.TAKE_SEAT, props=dict(seat_idx=123456))
    # подтверждение
    assert not db._events

    # садимся на место 7
    async with db:
        await table.handle_cmd(db, cmd_id=18, user_id=USER_ID, client_id=100, cmd_type=Command.Type.TAKE_SEAT, props=dict(seat_idx=7))
    # подтверждение
    assert len(db._events) == 1
    assert db._event.table_id == TABLE_ID
    assert db._event.msg_type == Message.Type(PLAYER_SEAT_EVENT_TYPE)

    # сел на место 7
    user, seat_idx, _ = table.find_user(USER_ID)
    assert user and user.id == USER_ID
    assert user.balance == BUYIN_VALUE
    assert user.connected
    assert user.clients == {100, 101, 110}
    assert seat_idx == 7
    assert table.seats[seat_idx] == user
    assert all(s is None for i, s in enumerate(table.seats) if i!=seat_idx)

    # выходим со стола (выход запрещен)
    table._user_exit_enabled = False
    async with db:
        await  table.handle_cmd(db, cmd_id=19, user_id=USER_ID, client_id=100, cmd_type=Command.Type.EXIT, props={})
    assert not db._events

    assert user and user.id == USER_ID
    assert user.balance == BUYIN_VALUE
    assert user.connected
    assert user.clients == {100, 101, 110}
    assert seat_idx == 7
    assert table.seats[seat_idx] == user
    assert all(s is None for i, s in enumerate(table.seats) if i!=seat_idx)

    # выходим со стола (выход разрешен)
    table._user_exit_enabled = True
    async with db:
        await  table.handle_cmd(db, cmd_id=20, user_id=USER_ID, client_id=100, cmd_type=Command.Type.EXIT, props={})
    assert len(db._events) == 1
    assert db._event.table_id == TABLE_ID
    assert db._event.msg_type == Message.Type(PLAYER_EXIT_EVENT_TYPE)

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
        await  table.handle_cmd(db, cmd_id=21, user_id=123456, client_id=100, cmd_type=Command.Type.EXIT, props={})
    assert not db._events

    # c запросом места (посадка разрешена)
    table._user_enter_enabled = True
    async with db:
        await table.handle_cmd(db, cmd_id=22, user_id=USER_ID, client_id=111, cmd_type=Command.Type.JOIN, props=dict(take_seat=True))
    # подтверждение подключения
    assert len(db._events) == 2
    e201 = db._events[0]
    assert e201.table_id == TABLE_ID
    assert e201.msg_type == Message.Type(PLAYER_ENTER_EVENT_TYPE)
    assert e201.client_id is None
    e101 = db._events[1]
    assert e101.table_id == TABLE_ID
    assert e101.msg_type == Message.Type(TABLE_INFO_EVENT_TYPE)
    assert e101.client_id==111

    # сел на место 0
    user, seat_idx, _ = table.find_user(USER_ID)
    assert user and user.id == USER_ID
    assert user.balance == BUYIN_VALUE
    assert user.connected
    assert user.clients == {100, 101, 110, 111}
    assert seat_idx == 0
    assert table.seats[seat_idx] == user
    assert all(s is None for i, s in enumerate(table.seats) if i!=seat_idx)

    # ПОЛЬЗОВАТЕЛЬ УЖЕ ЗА СТОЛОМ

    # подключаемся без места (посадка запрещена)
    table._user_enter_enabled = False
    async with db:
        await table.handle_cmd(db, cmd_id=31, user_id=USER_ID, client_id=200, cmd_type=Command.Type.JOIN, props=dict(take_seat=False))
    # подтверждение подключения
    assert len(db._events) == 1
    assert db._event.table_id == TABLE_ID
    assert db._event.msg_type == Message.Type(TABLE_INFO_EVENT_TYPE)
    assert db._event.client_id==200
    
    user, seat_idx, _ = table.find_user(USER_ID)
    assert user and user.id == USER_ID
    assert user.balance == BUYIN_VALUE
    assert user.connected
    assert user.clients == {100, 101, 110, 111, 200}
    assert seat_idx == 0
    assert table.seats[seat_idx] == user
    assert all(s is None for i, s in enumerate(table.seats) if i!=seat_idx)

    # c запросом места (посадка запрещена)
    table._user_enter_enabled = False
    async with db:
        await table.handle_cmd(db, cmd_id=32, user_id=USER_ID, client_id=201, cmd_type=Command.Type.JOIN, props=dict(take_seat=True))
    # подтверждение подключения
    assert len(db._events) == 1
    assert db._event.table_id == TABLE_ID
    assert db._event.msg_type == Message.Type(TABLE_INFO_EVENT_TYPE)
    assert db._event.client_id==201

    user, seat_idx, _ = table.find_user(USER_ID)
    assert user and user.id == USER_ID
    assert user.balance == BUYIN_VALUE
    assert user.connected
    assert user.clients == {100, 101, 110, 111, 200, 201}
    assert seat_idx == 0
    assert table.seats[seat_idx] == user
    assert all(s is None for i, s in enumerate(table.seats) if i!=seat_idx)

    # без места (посадка разрешена)
    table._user_enter_enabled = True
    async with db:
        await table.handle_cmd_join(db, cmd_id=33, user_id=USER_ID, client_id=210, take_seat=False)
    # подтверждение подключения
    assert len(db._events) == 1
    assert db._event.table_id == TABLE_ID
    assert db._event.msg_type == Message.Type(TABLE_INFO_EVENT_TYPE)
    assert db._event.client_id==210

    user, seat_idx, _ = table.find_user(USER_ID)
    assert user and user.id == USER_ID
    assert user.balance == BUYIN_VALUE
    assert user.connected
    assert user.clients == {100, 101, 110, 111, 200, 201, 210}
    assert seat_idx == 0
    assert table.seats[seat_idx] == user
    assert all(s is None for i, s in enumerate(table.seats) if i!=seat_idx)

    # c запросом места (посадка разрешена)
    table._user_enter_enabled = True
    async with db:
        await table.handle_cmd(db, cmd_id=34, user_id=USER_ID, client_id=211, cmd_type=Command.Type.JOIN, props=dict(take_seat=True))
    # подтверждение подключения
    assert len(db._events) == 1
    assert db._event.table_id == TABLE_ID
    assert db._event.msg_type == Message.Type(TABLE_INFO_EVENT_TYPE)
    assert db._event.client_id==211

    user, seat_idx, _ = table.find_user(USER_ID)
    assert user and user.id == USER_ID
    assert user.balance == BUYIN_VALUE
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
        assert user.balance == BUYIN_VALUE
        assert user.connected
        assert client_id not in user.clients
        assert seat_idx == 0
        assert table.seats[seat_idx] == user
        assert all(s is None for i, s in enumerate(table.seats) if i!=seat_idx)
    assert user.clients == {210, 211}

    # выходим со стола
    async with db:
        await  table.handle_cmd(db, cmd_id=35, user_id=USER_ID, client_id=210, cmd_type=Command.Type.EXIT, props={})
    assert len(db._events) == 1
    assert db._event.table_id == TABLE_ID
    assert db._event.msg_type == 299

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

@pytest.mark.dependency(depends=["test_user_lifecycle"])
@pytest.mark.asyncio
async def test_run_all_together():
    TABLE_ID = 777
    X_DBI._events_keep = True
    db = X_DBI()
    table = X_Table(TABLE_ID, 2)
    table.NEW_GAME_DELAY = 1

    async def stop_game(timeout=10):
        for _ in range(timeout*10):
            await asyncio.sleep(0.1)
            async with table.lock:
                if table.game:
                    table.game._stop = True
                    break

    await table.start()
    await asyncio.sleep(1)
    for i in range(1, 2):
        async with db:
            await table.handle_cmd(db, cmd_id=100+i, user_id=i*10, client_id=i*100, cmd_type=Command.Type.JOIN, props=dict(take_seat=True))
        if i<2:
            continue
    for i in range(2, 8):
        async with db:
            await table.handle_cmd(db, cmd_id=200+i, user_id=i*10, client_id=i*100, cmd_type=Command.Type.JOIN, props=dict(take_seat=True))
        await stop_game()
    for i in range(60):
        async with table.lock:
            players = [u for u in table.seats if u]
            if len(players)<2:
                break
            if table.game:
                table.game._stop = True
        await asyncio.sleep(1)

    await table.stop()

#    for x in db._events:
#        logger.info("%s: %s", x.msg_type, x.props)
