import pytest
import pytest_asyncio

from fastapi.testclient import TestClient
from ravvi_poker.api.app import app
from ravvi_poker.api.auth_.types import UserAccessProfile
from ravvi_poker.engine.tables import TablesManager

import logging
logger = logging.getLogger(__name__)

@pytest.fixture()
def api_client():
    client = TestClient(app)
    yield client

@pytest.fixture
def api_guest(api_client: TestClient):
    response = api_client.post("/v1/auth/register", json={})
    assert response.status_code == 200
    yield UserAccessProfile(**response.json())

@pytest.fixture
def api_client_2():
    client = TestClient(app)
    yield client

@pytest.fixture
def api_client_3():
    client = TestClient(app)
    yield client

@pytest.fixture
def api_guest_2(api_client: TestClient):
    response = api_client.post("/v1/auth/register", json={})
    assert response.status_code == 200
    yield UserAccessProfile(**response.json())

@pytest.fixture
def api_guest_3(api_client: TestClient):
    response = api_client.post("/v1/auth/register", json={})
    assert response.status_code == 200
    yield UserAccessProfile(**response.json())
