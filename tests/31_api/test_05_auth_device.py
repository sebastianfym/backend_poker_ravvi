import pytest
pytestmark = pytest. mark. skip()

from fastapi.testclient import TestClient

from ravvi_poker.api.app import app

client = TestClient(app)


def register_guest():
    response = client.post("/v1/auth/register", json={})
    assert response.status_code == 200
    result = response.json()
    device_token = result["device_token"]
    access_token = result["access_token"]
    return access_token, device_token


def test_auth_device():
    # register new guest
    access_token, device_token = register_guest()
    # headers = {"Authorization": "Bearer " + access_token}

    params = dict(device_token=device_token, device_info={})
    response = client.post("/v1/auth/device", json=params)
    assert response.status_code == 200

    result = response.json()
    assert result["device_token"] == device_token
    assert result["access_token"] != access_token
    assert isinstance(result["user_id"], int)
    assert isinstance(result["username"], str)
