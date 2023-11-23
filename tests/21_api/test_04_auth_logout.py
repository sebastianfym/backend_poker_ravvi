import pytest
pytestmark = pytest. mark. skip()

from fastapi.testclient import TestClient

from ravvi_poker.api.main import app

client = TestClient(app)


def register_guest():
    response = client.post("/v1/auth/register", json={})
    assert response.status_code == 200
    result = response.json()
    username = result["username"]
    device_token = result["device_token"]
    access_token = result["access_token"]

    return username, device_token, access_token


def test_register_and_logout():
    # register new guest
    username, device_token, access_token = register_guest()
    headers = {"Authorization": "Bearer " + access_token}

    # try correct params
    response1 = client.post("/v1/auth/logout", headers=headers)
    assert response1.status_code == 200

    result1 = response1.json()
    assert result1
    assert isinstance(result1["device_token"], str)
    assert result1["access_token"] is None
    assert result1["user_id"] is None
    assert result1["username"] is None
