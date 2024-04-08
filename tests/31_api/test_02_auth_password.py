import pytest

from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN, HTTP_422_UNPROCESSABLE_ENTITY
from fastapi.testclient import TestClient
from ravvi_poker.api.auth.types import UserAccessProfile

def test_change_password(api_client: TestClient, api_guest: UserAccessProfile):
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}

    params = dict(new_password="test")
    response = api_client.post("/api/v1/auth/password", json=params)
    assert response.status_code == 200

    params = dict(new_password="new_test", current_password="test")
    response = api_client.post("/api/v1/auth/password", json=params)
    assert response.status_code == 200

    # logout
    response = api_client.post("/api/v1/auth/logout")
    assert response.status_code == 200


#@pytest.mark.skip
def test_change_password_negative(api_client: TestClient, api_guest: UserAccessProfile):
    # try w/o access_token
    response = api_client.post("/api/v1/auth/password", headers=None, json=None)
    assert response.status_code == HTTP_401_UNAUTHORIZED

    # set headers
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}

    # try no params
    response = api_client.post("/api/v1/auth/password", json=None)
    assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY

    # try bad password
    params = dict(new_password="")
    response = api_client.post("/api/v1/auth/password", json=params)
    assert response.status_code == HTTP_400_BAD_REQUEST

    # try wrong current password
    params = dict(current_password="wrong", new_password="test")
    response = api_client.post("/api/v1/auth/password", json=params)
    assert response.status_code == HTTP_401_UNAUTHORIZED

    # set password
    params = dict(new_password="test")
    response = api_client.post("/api/v1/auth/password", json=params)
    assert response.status_code == 200

    # try wrong empty password
    params = dict(current_password="", new_password="new_test")
    response = api_client.post("/api/v1/auth/password", json=params)
    assert response.status_code == 401

    # try wrong empty password
    params = dict(current_password="wrong", new_password="new_test")
    response = api_client.post("/api/v1/auth/password", json=params)
    assert response.status_code == 401

    # logout
    response = api_client.post("/api/v1/auth/logout")
    assert response.status_code == 200


def test_auth_different_authorization_methods_and_password(api_client: TestClient, api_guest: UserAccessProfile):
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}

    params = dict(new_password="test_password")
    response = api_client.post("/api/v1/auth/password", json=params)
    assert response.status_code == 200

    params = {
        "username": api_guest.user.name,
        "password": "test_password"
    }
    response = api_client.post(f'/api/v1/auth/login', json=params)
    assert response.status_code == 200

    params = {
        "username": f"{api_guest.user.id}",
        "password": "test_password"
    }
    response = api_client.post(f'/api/v1/auth/login', json=params)
    assert response.status_code == 200

    params = {
        "username": "test_email@mail.ru"
    }
    response = api_client.patch(f'/api/v1/user/profile', json=params)
    assert response.status_code == 200

    params = {
        "username": "test_email@mail.ru",
        "password": "test_password35325"
    }
    response = api_client.post(f'/api/v1/auth/login', json=params)
    assert response.status_code == 401
