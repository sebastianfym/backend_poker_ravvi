import logging
import pytest
import pytest_asyncio
import asyncio

from ravvi_poker.db import DBI
from ravvi_poker.engine.tables import TablesManager
from ravvi_poker.engine.clients.manager import ClientsManager
from ravvi_poker.bots.dummy import DummyBot

log = logging.getLogger(__name__)

async def create_user(balance=0):
    async with DBI(log=log) as db:
        user = await db.create_user(balance=balance)    
    return user

async def create_client(user):
    async with DBI(log=log) as db:
        device = await db.create_device()
        login = await db.create_login(device.id, user.id)
        session = await db.create_session(login.id)
        client = await db.create_client(session.id)
    return client

async def create_table():
    async with DBI(log=log) as db:
        table = await db.create_table(table_type="RG", table_seats=9, table_name="test_01_rg", 
            game_type="NLH", game_subtype="REGULAR", club_id=0,
            props=dict(
                buyin_min = 2,
                bet_timeout = 10,
                blind_small = 5,
            ))
    return table

async def send_cmd_table_join(client, table):
    async with DBI() as db:
        await db.create_table_cmd(client_id=client.id, table_id=table.id, cmd_type=11, props=dict(take_seat=True))


async def wait_for_no_players(x_table):
    while True:
        players = [u for u in x_table.seats if u]
        if len(players)<2:
            break
        await asyncio.sleep(1)

@pytest_asyncio.fixture()
async def engine():
    await DBI.pool_open()
    # закрыть все существующие столы (невидимы для engine manager)
    async with DBI(log=log) as db:
        await db.dbi.execute('UPDATE table_profile SET closed_ts=now_utc()')
    t_mgr = TablesManager()
    await t_mgr.start()
    c_mgr = ClientsManager()
    await c_mgr.start()
    yield t_mgr, c_mgr
    await t_mgr.stop()
    await c_mgr.stop()
    await DBI.pool_close()
    await asyncio.sleep(1)

@pytest.mark.asyncio
async def test_engine_manager(engine):
    t_mgr, c_mgr = engine

    # создадим один стол
    log.info('create table ...')
    table = await create_table()
    log.info('create table: done')
    await asyncio.sleep(1)

    # проверяем что стол запущен
    assert table.id in t_mgr.tables
    x_table = t_mgr.tables[table.id]

    # bot-1
    user_1 = await create_user(2)
    client_1 = await create_client(user_1)
    c1 = DummyBot(c_mgr, client_1.id, user_1.id)
    await c1.start()
    await c1.join_table(table.id)

    await asyncio.sleep(3)
    assert user_1.id in x_table.users
    assert user_1.id in [u.id for u in x_table.seats if u]

    user_2 = await create_user(10)
    client_2 = await create_client(user_2)
    c2 = DummyBot(c_mgr, client_2.id, user_2.id)
    await c2.start()
    await c2.join_table(table.id)
    log.info('game should start soon ...')

    await asyncio.sleep(1)
    assert user_2.id in x_table.users
    assert user_2.id in [u.id for u in x_table.seats if u]

    log.info('wait_for_no_players ...')
    await wait_for_no_players(x_table)

    await c1.shutdown()
    await c2.shutdown()
