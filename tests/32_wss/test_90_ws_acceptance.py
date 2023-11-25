import logging
import asyncio
import time
import pytest
import pytest_asyncio

from urllib.parse import urlencode
from fastapi import WebSocketException, WebSocketDisconnect, WebSocket
from fastapi.testclient import TestClient

from ravvi_poker.ws.app import app, manager

@pytest.fixture(autouse=True, scope='module')
def test_client():
    with TestClient(app) as test_client:
        yield test_client

def test_ws_invalid_access_token(test_client: TestClient):
    access_token = 'invalid'
    params = urlencode(dict(access_token=access_token))
    with pytest.raises(WebSocketDisconnect) as ex_info:
        with test_client.websocket_connect(f"/v1/ws?{params}") as ws:
            pass
    assert ex_info.value.code == 1008

def test_ws_connect(test_client: TestClient, access):
    session_info, access_token = access

    params = urlencode(dict(access_token=access_token))
    with test_client.websocket_connect(f"/v1/ws?{params}") as ws:
        assert manager.clients
