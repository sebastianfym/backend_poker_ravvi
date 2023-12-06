import pytest

from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN, HTTP_422_UNPROCESSABLE_ENTITY
from fastapi.testclient import TestClient
from ravvi_poker.api.auth import UserAccessTokens


def test_auth_login(api_client: TestClient, api_guest: UserAccessTokens):

    # set headers
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}
    
    # change password
    params = dict(new_password="test")
    response = api_client.post("/v1/auth/password", json=params)
    assert response.status_code == 200

    # logout
    response = api_client.post("/v1/auth/logout")
    assert response.status_code == 200

    api_client.headers = None

    # try user id
    params = dict(username=str(api_guest.user_id), password="test", client_id=api_guest.device_token)
    response = api_client.post("/v1/auth/login", data=params)
    assert response.status_code == 200
    result = UserAccessTokens(**response.json())
    assert result.device_token == api_guest.device_token
    assert result.login_token != api_guest.login_token
    assert result.access_token is not None

    api_client.headers = {"Authorization": "Bearer " + result.access_token}

    # logout
    response = api_client.post("/v1/auth/logout")
    assert response.status_code == 200
