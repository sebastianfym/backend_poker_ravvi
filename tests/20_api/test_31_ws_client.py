import pytest
from urllib.parse import urlencode
from fastapi import WebSocketException, WebSocketDisconnect
from fastapi.testclient import TestClient

from ravvi_poker.api.main import app as api_app
from ravvi_poker.ws.app import app as ws_app

api_test = TestClient(api_app)
ws_test = TestClient(ws_app)

def register_guest():
    response = api_test.post("/v1/auth/register", json={})
    assert response.status_code == 200
    result = response.json()
    username = result["username"]
    access_token = result["access_token"]
    return access_token, username

def test_01_ws_broken_access_token():
    with ws_test:
        access_token = 'broken'
        params = urlencode(dict(access_token=access_token))
        with pytest.raises(WebSocketDisconnect) as ex_info:
            with ws_test.websocket_connect(f"/v1/ws?{params}") as ws:
                pass
        assert ex_info.value.code == 1008

def test_02_ws_valid_token():
    # register new guest
    access_token, username = register_guest()

    with ws_test:
        params = urlencode(dict(access_token=access_token))
        with ws_test.websocket_connect(f"/v1/ws?{params}") as ws:
            pass

if __name__=='__main__':
    test_02_ws_valid_token()