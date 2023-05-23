from fastapi.testclient import TestClient

from ravvi_poker.api.main import app

client = TestClient(app)


def test_auth_register():
    # CASE 1: register guest on new device
    params1 = dict(device_token=None, device_props={})
    response1 = client.post("/v1/auth/register", json=params1)
    assert response1.status_code == 200

    result1 = response1.json()
    assert result1
    assert isinstance(result1["device_token"], str)
    assert isinstance(result1["access_token"], str)
    assert result1["token_type"] == "bearer"
    assert isinstance(result1["user_id"], int)
    assert isinstance(result1["username"], str)

    # CASE 2: register guest on known device
    params2 = dict(device_token=result1["device_token"], device_props={})
    response2 = client.post("/v1/auth/register", json=params2)
    assert response2.status_code == 200

    result2 = response2.json()
    assert result2
    assert isinstance(result2["device_token"], str)
    assert result2["device_token"] != result1["device_token"]
    assert isinstance(result2["access_token"], str)
    assert result2["access_token"] != result1["access_token"]
    assert result2["token_type"] == "bearer"
    assert isinstance(result2["user_id"], int)
    assert isinstance(result2["username"], str)
