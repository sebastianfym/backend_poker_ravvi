import pytest
import pytest_asyncio

from fastapi.testclient import TestClient
from ravvi_poker.api.app import app
from ravvi_poker.api.auth import UserAccessTokens

@pytest.fixture
def api_client():
    client = TestClient(app)
    yield client

@pytest.fixture
def api_guest(api_client: TestClient):
    response = api_client.post("/v1/auth/register", json={})
    assert response.status_code == 200
    yield UserAccessTokens(**response.json())
