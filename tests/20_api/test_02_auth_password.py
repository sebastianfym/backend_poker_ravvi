from fastapi.testclient import TestClient

from ravvi_poker.api.main import app

client = TestClient(app)


def register_guest():
    response = client.post("/v1/auth/register", json={})
    assert response.status_code == 200
    result = response.json()
    access_token = result["access_token"]
    return access_token


def test_change_password():
    # register new guest
    access_token = register_guest()
    headers = {"Authorization": "Bearer " + access_token}

    params = dict(new_password="test")
    response = client.post("/v1/auth/password", headers=headers, json=params)
    assert response.status_code == 200

    params = dict(new_password="new_test", current_password="test")
    response = client.post("/v1/auth/password", headers=headers, json=params)
    assert response.status_code == 200


def test_change_password_negative():
    # register new guest
    access_token = register_guest()
    headers = {"Authorization": "Bearer " + access_token}

    # try w/o access_token
    response = client.post("/v1/auth/password", headers=None, json=None)
    assert response.status_code == 401

    # try no params
    response = client.post("/v1/auth/password", headers=headers, json=None)
    assert response.status_code == 422

    # try bad password
    params = dict(new_password="")
    response = client.post("/v1/auth/password", headers=headers, json=params)
    assert response.status_code == 400

    # try wrong current password
    params = dict(current_password="something", new_password="test")
    response = client.post("/v1/auth/password", headers=headers, json=params)
    assert response.status_code == 401

    # set password
    params = dict(new_password="test")
    response = client.post("/v1/auth/password", headers=headers, json=params)
    assert response.status_code == 200

    # try wrong current password
    params = dict(current_password="something", new_password="new_test")
    response = client.post("/v1/auth/password", headers=headers, json=params)
    assert response.status_code == 401
