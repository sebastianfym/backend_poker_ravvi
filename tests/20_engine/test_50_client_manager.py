import logging
import pytest
import pytest_asyncio
import asyncio

from ravvi_poker.db import DBI
from ravvi_poker.engine.events import Message
from ravvi_poker.engine.clients import ClientsManager, ClientBase, ClientQueue

log = logging.getLogger(__name__)

async def create_user():
    async with DBI() as db:
        user = await db.create_user()    
    return user

async def create_client(user):
    async with DBI() as db:
        device = await db.create_device()
        login = await db.create_login(device.id, user.id, host="127.0.0.1")
        session = await db.create_session(login.id, host="127.0.0.1")
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


class X_ClientBase(ClientBase):

    def __init__(self, manager, client_id, user_id) -> None:
        super().__init__(manager, client_id, user_id)
        self.messages : list[Message] = []

    async def on_msg(self, msg: Message):
        self.log.info("msg: %s", msg)
        self.messages.append(msg)

class X_ClientQueue(ClientQueue):

    def __init__(self, manager, client_id, user_id) -> None:
        super().__init__(manager, client_id, user_id)
        self.messages : list[Message] = []

    async def on_msg(self, msg: Message):
        self.log.info("msg: %s", msg)
        self.messages.append(msg)


@pytest_asyncio.fixture()
async def clients_manager():
    #await DBI.pool_open()
    manager = ClientsManager()
    await manager.start()
    yield manager
    await manager.stop()
    #await DBI.pool_close()
    await asyncio.sleep(1)

@pytest.mark.asyncio
async def test_client_base(clients_manager: ClientsManager):
    # создадим стол для целостности ссылок
    table = await create_table()

    # пользователь/клиент
    user = await create_user()
    client = await create_client(user)
    # тестовый клиент
    x = X_ClientBase(clients_manager, client.id, user.id)
    await x.start()

    # TABLE_INFO
    async with DBI() as db:
        await db.create_table_msg(client_id=x.client_id, table_id=table.id, game_id=None, msg_type=Message.Type.TABLE_INFO, props=dict(table_redirect_id=table.id))
    # время на обработку
    await asyncio.sleep(1)

    # проверка получения сообщения
    assert x.messages
    msg = x.messages[0]
    # проверка сообщения
    assert msg.msg_type == Message.Type.TABLE_INFO
    # проверка подписки клиента
    assert table.id in x.tables
    subscribers = clients_manager.table_subscribers.get(table.id, None)
    assert subscribers
    assert x.client_id in subscribers

    #await x.shutdown()
    #await asyncio.sleep(10)
    

@pytest.mark.asyncio
async def test_client_queue(clients_manager: ClientsManager):
    # создадим стол для целостности ссылок
    table = await create_table()

    # пользователь/клиент
    user = await create_user()
    client = await create_client(user)
    # тестовый клиент
    x = X_ClientQueue(clients_manager, client.id, user.id)
    await x.start()
    # TABLE_INFO
    async with DBI() as db:
        await db.create_table_msg(client_id=x.client_id, table_id=table.id, game_id=None, msg_type=Message.Type.TABLE_INFO, props=dict(table_redirect_id=table.id))
    # время на обработку
    await asyncio.sleep(1)

    # проверка получения сообщения
    assert x.messages
    msg = x.messages[0]
    # проверка сообщения
    assert msg.msg_type == Message.Type.TABLE_INFO
    # проверка подписки клиента
    assert table.id in x.tables
    subscribers = clients_manager.table_subscribers.get(table.id, None)
    assert subscribers
    assert x.client_id in subscribers
