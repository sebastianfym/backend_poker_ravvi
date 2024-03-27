import pytest

from starlette.status import HTTP_200_OK
from fastapi.testclient import TestClient
from ravvi_poker.api.auth_.types import UserAccessProfile


def test_lobby_(api_client: TestClient, api_guest: UserAccessProfile):
    # set headers
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}

    response = api_client.get("/v1/lobby/entry_tables")
    assert response.status_code == HTTP_200_OK
