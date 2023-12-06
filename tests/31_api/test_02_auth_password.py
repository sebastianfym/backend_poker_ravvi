import pytest

from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN, HTTP_422_UNPROCESSABLE_ENTITY
from fastapi.testclient import TestClient
from ravvi_poker.api.auth import UserAccessProfile

def test_change_password(api_client: TestClient, api_guest: UserAccessProfile):
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}

    params = dict(new_password="test")
    response = api_client.post("/v1/auth/password", json=params)
    assert response.status_code == 200

    params = dict(new_password="new_test", current_password="test")
    response = api_client.post("/v1/auth/password", json=params)
    assert response.status_code == 200

    # logout
    response = api_client.post("/v1/auth/logout")
    assert response.status_code == 200


#@pytest.mark.skip
def test_change_password_negative(api_client: TestClient, api_guest: UserAccessProfile):
    # try w/o access_token
    response = api_client.post("/v1/auth/password", headers=None, json=None)
    assert response.status_code == HTTP_401_UNAUTHORIZED

    # set headers
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}

    # try no params
    response = api_client.post("/v1/auth/password", json=None)
    assert response.status_code == HTTP_422_UNPROCESSABLE_ENTITY

    # try bad password
    params = dict(new_password="")
    response = api_client.post("/v1/auth/password", json=params)
    assert response.status_code == HTTP_400_BAD_REQUEST

    # try wrong current password
    params = dict(current_password="wrong", new_password="test")
    response = api_client.post("/v1/auth/password", json=params)
    assert response.status_code == HTTP_401_UNAUTHORIZED

    # set password
    params = dict(new_password="test")
    response = api_client.post("/v1/auth/password", json=params)
    assert response.status_code == 200

    # try wrong empty password
    params = dict(current_password="", new_password="new_test")
    response = api_client.post("/v1/auth/password", json=params)
    assert response.status_code == 401

    # try wrong empty password
    params = dict(current_password="wrong", new_password="new_test")
    response = api_client.post("/v1/auth/password", json=params)
    assert response.status_code == 401

    # logout
    response = api_client.post("/v1/auth/logout")
    assert response.status_code == 200
