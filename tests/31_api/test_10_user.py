import pytest

from starlette.status import HTTP_200_OK, HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN, HTTP_422_UNPROCESSABLE_ENTITY
from fastapi.testclient import TestClient
from ravvi_poker.api.auth import UserAccessTokens
from ravvi_poker.api.user import UserPrivateProfile, UserPublicInfo


def test_user(api_client: TestClient, api_guest: UserAccessTokens, api_client_2: TestClient, api_guest_2: UserAccessTokens):
    # set headers
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}
    api_client_2.headers = {"Authorization": "Bearer " + api_guest_2.access_token}

    response = api_client.get("/v1/user/profile")
    assert response.status_code == HTTP_200_OK
    user_1 = UserPrivateProfile(**response.json())
    assert user_1.id == api_guest.user_id
    assert user_1.username
    assert user_1.image_id is None
    assert user_1.has_password == False
    assert user_1.email is None

    response = api_client.get(f"/v1/user/{api_guest_2.user_id}")
    assert response.status_code == HTTP_200_OK
    user_2 = UserPublicInfo(**response.json())
    assert user_2.id == api_guest_2.user_id
    assert user_2.username
    assert user_2.image_id is None

    # update own data
    params = {'aaabbbccc': 'test', 'username': 'test1'}
    response = api_client.patch("/v1/user/profile", json=params)
    assert response.status_code == HTTP_200_OK
    user_1 = UserPrivateProfile(**response.json())
    assert user_1.id == api_guest.user_id
    assert user_1.username == 'test1'
    assert user_1.image_id is None
    assert user_1.has_password == False
    assert user_1.email is None

    params = {'username': 'test2', 'image_id': 11}
    response = api_client.patch("/v1/user/profile", json=params)
    assert response.status_code == HTTP_200_OK
    user_1 = UserPrivateProfile(**response.json())
    assert user_1.id == api_guest.user_id
    assert user_1.username == 'test2'
    assert user_1.image_id == 11
    assert user_1.has_password == False
    assert user_1.email is None

    response = api_client_2.get(f"/v1/user/{api_guest.user_id}")
    assert response.status_code == HTTP_200_OK
    user_1 = UserPublicInfo(**response.json())
    assert user_1.id == api_guest.user_id
    assert user_1.username == 'test2'
    assert user_1.image_id == 11
