import pytest
import asyncio
import pytest
from urllib.parse import urlencode
from fastapi import WebSocketException, WebSocketDisconnect, WebSocket
from fastapi.testclient import TestClient
from httpx import AsyncClient

from ravvi_poker.api.main import app as api_app
from ravvi_poker.ws.app import app as ws_app, manager as ws_mgr
from ravvi_poker.engine.main import start_engine, stop_engine

api_test = TestClient(api_app)
ws_test = TestClient(ws_app)



def register_guest():
    response = api_test.post("/v1/auth/register", json={})
    assert response.status_code == 200
    result = response.json()
    username = result["username"]
    access_token = result["access_token"]
    return access_token, username

@pytest.mark.asyncio
async def test_10_engine():
    engine = await start_engine()
    await ws_mgr.start()
    
    await asyncio.sleep(2)

    # register new guest
    access_token, username = register_guest()

    #with ws_test:
    params = urlencode(dict(access_token=access_token))
    with ws_test.websocket_connect(f"/v1/ws?{params}") as ws:
        s : WebSocket = ws
        ws.send_json(dict(type=11, table_id=11))
        await asyncio.sleep(10)
        r = ws.receive_json()
        print(r)

    await asyncio.sleep(2)

    await ws_mgr.stop()
    await stop_engine(engine)


if __name__=='__main__':
    import logging
    logging.basicConfig(level=logging.DEBUG)
    import asyncio
    asyncio.run(test_10_engine())