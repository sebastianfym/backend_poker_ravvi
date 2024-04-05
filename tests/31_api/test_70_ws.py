import pytest
import pytest_asyncio
from urllib.parse import urlencode
from time import sleep
from fastapi import WebSocketException, WebSocketDisconnect
from fastapi.testclient import TestClient
from httpx import AsyncClient

from ravvi_poker.db import DBI
from ravvi_poker.engine.tables import TablesManager
from ravvi_poker.api.auth.types import UserAccessProfile

import logging
logger = logging.getLogger(__name__)

@pytest.mark.skip
def test_ws_no_token(api_client: TestClient):
    # set headers
    with pytest.raises(WebSocketDisconnect) as ex_info:
        with api_client.websocket_connect("/api/v1/ws") as ws:
            pass
    assert ex_info.value.code == 1008

@pytest.mark.skip
def test_ws_valid_token(api_client: TestClient, api_guest: UserAccessProfile):
    params = urlencode(dict(access_token=api_guest.access_token))
    with api_client.websocket_connect(f"/api/v1/ws?{params}") as ws:
        sleep(3)
        ws.close()
        sleep(1)

def cmd_TABLE_JOIN(ws, **kwargs):
    #import json
    cmd = dict(cmd_type=11, **kwargs)
    #cmd = json.dumps(cmd)
    logger.info("cmd %s", cmd)
    ws.send_json(cmd)

#@pytest.mark.asyncio    
def test_ws_join(api_client: TestClient, api_guest: UserAccessProfile, table):
    params = urlencode(dict(access_token=api_guest.access_token))
    with api_client.websocket_connect(f"/api/v1/ws?{params}") as ws:
        cmd_TABLE_JOIN(ws, table_id=table.id, take_seat=True)
        msg = ws.receive_json()
        logger.info("got %s", msg)
    assert msg.get('msg_type') == 102
    assert msg.get('table_id') == table.id

