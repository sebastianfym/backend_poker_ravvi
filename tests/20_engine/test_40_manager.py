import logging
import pytest
import pytest_asyncio
import asyncio

from ravvi_poker.db import DBI
from ravvi_poker.engine.manager import Engine_Manager

log = logging.getLogger(__name__)

async def create_user():
    async with DBI() as db:
        user = await db.create_user()    
    return user

async def create_client(user):
    async with DBI() as db:
        device = await db.create_device()
        login = await db.create_login(device.id, user.id)
        session = await db.create_session(login.id)
        client = await db.create_client(session.id)
    return client

async def create_table():
    async with DBI() as db:
        table = await db.create_table(table_type="RG", table_seats=9, table_name="PUBLIC", 
            game_type="NLH", game_subtype="REGULAR", 
            props=dict(
                bet_timeout = 1,
            ))
    return table

async def send_cmd_table_join(client, table):
    async with DBI() as db:
        await db.create_table_cmd(client_id=client.id, table_id=table.id, cmd_type=11, props=dict(take_seat=True))


@pytest_asyncio.fixture()
async def engine():
    #await DBI.pool_open()
    manager = Engine_Manager()
    #await manager.start()
    yield manager
    await manager.stop()
    #await DBI.pool_close()
    await asyncio.sleep(1)

@pytest.mark.asyncio
async def test_engine_manager(engine):

    # закрыть все существующие столы (невидимы для engine manager)
    async with DBI() as db:
        await db.dbi.execute('UPDATE table_profile SET closed_ts=now_utc()')

    # создадим один стол до старта engine
    table_1 = await create_table()

    # запуск engine       
    await engine.start()
    
    # проверяем что существующий стол подхвачен  запущен
    assert table_1.id in engine.tables
    x_table = engine.tables[table_1.id]


    # два пользователя/клиента
    user_1 = await create_user()
    client_1 = await create_client(user_1)
    await send_cmd_table_join(client_1, table_1)
    await asyncio.sleep(1)
    assert user_1.id in x_table.users
    assert user_1.id in [u.id for u in x_table.seats if u]


    user_2 = await create_user()
    client_2 = await create_client(user_2)
    await send_cmd_table_join(client_2, table_1)
    await asyncio.sleep(1)
    assert user_2.id in x_table.users
    assert user_2.id in [u.id for u in x_table.seats if u]

    await asyncio.sleep(10)
    await engine.stop()
    assert not engine.tables
