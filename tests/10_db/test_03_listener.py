import pytest
import asyncio

from ravvi_poker.db import DBI, DBI_Listener

@pytest.mark.asyncio
async def test_client(client):
    x = DBI_Listener()
    await asyncio.wait_for(x.start(), timeout=10)
    await asyncio.sleep(1)
    await asyncio.wait_for(x.stop(), timeout=10)
    
