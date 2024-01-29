import pytest
from fastapi.testclient import TestClient
from ravvi_poker.api.auth import UserAccessProfile, UserPrivateProfile

def test_auth_register(api_client: TestClient):
    # CASE 1: register guest on new device
    params1 = dict(device_token=None, device_props={})
    response1 = api_client.post("/v1/auth/register", json=params1)
    assert response1.status_code == 200

    result1 = response1.json()
    assert result1
    assert isinstance(result1.get("device_token",None), str)
    assert isinstance(result1.get("login_token",None), str)
    assert isinstance(result1.get("access_token", None), str)
    assert result1["token_type"] == "bearer"
    user_1 = UserPrivateProfile(**result1["user"])
    assert isinstance(user_1.id, int)
    assert isinstance(user_1.name, str)

    # CASE 2: register guest on known device
    params2 = dict(device_token=result1["device_token"], device_props={})
    response2 = api_client.post("/v1/auth/register", json=params2)
    assert response2.status_code == 200

    result2 = response2.json()
    assert result2
    assert isinstance(result2["device_token"], str)
    assert result2["device_token"] == result1["device_token"]
    assert isinstance(result2.get("login_token",None), str)
    assert result2["login_token"] != result1["login_token"]
    assert isinstance(result2["access_token"], str)
    assert result2["access_token"] != result1["access_token"]
    assert result2["token_type"] == "bearer"
    user_2 = UserPrivateProfile(**result1["user"])
    assert isinstance(user_2.id, int)
    assert isinstance(user_2.name, str)

def test_auth_device_verify(api_client: TestClient, api_guest: UserAccessProfile):
    # проверка токена устройства и обновление информации
    params = dict(device_token=api_guest.device_token, device_info={})
    response = api_client.post("/v1/auth/device", json=params)
    assert response.status_code == 200

    # в ответ получаем токен устройства без login/access
    result = UserAccessProfile(**response.json())
    assert result.device_token == api_guest.device_token
    assert result.login_token is None
    assert result.access_token is None

def test_auth_device_login(api_client: TestClient, api_guest: UserAccessProfile):
    # авторизация с токенами устройства и логина
    params = dict(device_token=api_guest.device_token, login_token=api_guest.login_token, device_info={})
    response = api_client.post("/v1/auth/device", json=params)
    assert response.status_code == 200

    # в ответ получаем новый access
    result = UserAccessProfile(**response.json())
    assert result.device_token == api_guest.device_token
    assert result.login_token == api_guest.login_token
    assert result.access_token

    params1 = dict(device_token=None, device_props={})
    response1 = api_client.post("/v1/auth/register", json=params1)
    assert response1.status_code == 200

    params = dict(device_token=None, login_token=api_guest.login_token, device_info={})
    response = api_client.post("/v1/auth/device", json=params)
    assert response.status_code == 200
    assert response.json()['login_token'] is None
    assert response.json()['access_token'] is None
