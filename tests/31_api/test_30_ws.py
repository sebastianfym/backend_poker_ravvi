import pytest
pytestmark = pytest. mark. skip()

from urllib.parse import urlencode
from fastapi import WebSocketException, WebSocketDisconnect
from fastapi.testclient import TestClient

from ravvi_poker.api.app import app

client = TestClient(app)


def register_guest():
    response = client.post("/v1/auth/register", json={})
    assert response.status_code == 200
    result = response.json()
    username = result["username"]
    access_token = result["access_token"]
    return access_token, username


def test_01_ws_broken_access():
    access_token = 'broken'
    params = urlencode(dict(access_token=access_token))
    with pytest.raises(WebSocketDisconnect) as ex_info:
        with client.websocket_connect(f"/v1/ws?{params}") as websocket:
            pass
    assert ex_info.value.code == 1008
    
def test_02_ws_valid_token():
    # register new guest
    access_token, username = register_guest()

    params = urlencode(dict(access_token=access_token))
    with client.websocket_connect(f"/v1/ws?{params}") as websocket:
        pass

    access_token = 'broken'
    params = urlencode(dict(access_token=access_token))
    with pytest.raises(WebSocketDisconnect) as ex_info:
        with client.websocket_connect(f"/v1/ws?{params}") as websocket:
            pass
    assert ex_info.value.code == 1008
