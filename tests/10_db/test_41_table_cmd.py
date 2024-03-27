import logging
import pytest
import pytest_asyncio

from ravvi_poker.db.dbi import DBI
from helpers.x_listener import X_DBI_Listener


# from helpers.x_listener import X_DBI_Listener

@pytest.mark.asyncio
async def test_table_cmd_create(table, client):
    assert table
    assert client

    async with X_DBI_Listener("table_cmd") as x:
        async with DBI() as db:
            cmd = await db.create_table_cmd(client_id=client.id, table_id=table.id, cmd_type=777, props=None)
    assert x.expected and len(x.expected) == 1
    payload = x.expected[0]
    assert payload['cmd_id']
    assert payload['table_id'] ==  table.id

    async with DBI() as db:
        x = await db.get_table_cmd(payload['cmd_id'])
        assert x.client_id == client.id
        assert x.table_id == table.id
