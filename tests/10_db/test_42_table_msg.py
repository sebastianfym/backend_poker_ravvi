import logging
import pytest
import pytest_asyncio

from ravvi_poker.db.dbi import DBI
from tests.helpers.x_listener import X_DBI_Listener

@pytest.mark.asyncio
async def test_table_msg_create(table, client):
    assert table
    assert client

    async with X_DBI_Listener("table_msg") as x:
        async with DBI() as db:
            msg = await db.create_table_msg(table_id=table.id, game_id=None, msg_type=777, props=None)
        async with DBI() as db:
            msg = await db.create_table_msg(table_id=table.id, game_id=None, msg_type=777, props=None, client_id=client.id)
    assert x.expected and len(x.expected) == 2
    payload_1 = x.expected[0]
    assert payload_1['msg_id']
    assert payload_1['table_id'] ==  table.id
    payload_2 = x.expected[1]
    assert payload_1['msg_id']
    assert payload_1['table_id'] ==  table.id


    async with DBI() as db:
        x = await db.get_table_msg(payload_1['msg_id'])
        assert x.table_id == table.id
        assert not x.client_id

        x = await db.get_table_msg(payload_2['msg_id'])
        assert x.table_id == table.id
        assert x.client_id == client.id
