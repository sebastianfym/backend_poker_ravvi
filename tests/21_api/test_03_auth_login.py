import pytest
pytestmark = pytest. mark. skip()

from fastapi.testclient import TestClient

from ravvi_poker.api.main import app

client = TestClient(app)


def register_guest_and_set_password(password):
    response = client.post("/v1/auth/register", json={})
    assert response.status_code == 200
    result = response.json()
    username = result["username"]
    device_token = result["device_token"]
    access_token = result["access_token"]

    headers = {"Authorization": "Bearer " + access_token}
    params = dict(new_password="test")
    response = client.post("/v1/auth/password", headers=headers, json=params)
    assert response.status_code == 200

    return username, device_token


def test_auth_login():
    # register new guest
    username, device_token = register_guest_and_set_password("test")

    # try correct params
    params1 = dict(username=username, password="test", client_id=device_token)
    response1 = client.post("/v1/auth/login", data=params1)
    assert response1.status_code == 200

    result1 = response1.json()
    assert result1
    assert isinstance(result1["device_token"], str)
    assert isinstance(result1["access_token"], str)
    assert result1["token_type"] == "bearer"
    assert isinstance(result1["user_id"], int)
    assert isinstance(result1["username"], str)
