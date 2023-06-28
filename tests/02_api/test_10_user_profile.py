from fastapi.testclient import TestClient

from ravvi_poker.api.main import app

client = TestClient(app)


def register_guest():
    response = client.post("/v1/auth/register", json={})
    assert response.status_code == 200
    result = response.json()
    username = result["username"]
    access_token = result["access_token"]
    return access_token, username


def test_user_profile():
    # register new guest
    access_token, username = register_guest()
    headers = {"Authorization": "Bearer " + access_token}

    # check profile
    response = client.get("/v1/user/profile", headers=headers)
    assert response.status_code == 200
    profile1 = response.json()
    assert profile1["id"]
    assert profile1["username"] == username
    assert profile1["email"] is None
    assert profile1["has_password"] == False

    # set password
    params = dict(new_password="test")
    response = client.post("/v1/auth/password", headers=headers, json=params)
    assert response.status_code == 200

    # check profile
    response = client.get("/v1/user/profile", headers=headers)
    assert response.status_code == 200
    profile2 = response.json()
    assert profile2["id"] == profile1["id"]
    assert profile2["username"] == username
    assert profile2["email"] is None
    assert profile2["has_password"] == True


def test_user_profile_email():
    # register new guest
    access_token, username = register_guest()
    headers = {"Authorization": "Bearer " + access_token}

    # check profile
    response = client.get("/v1/user/profile", headers=headers)
    assert response.status_code == 200
    profile1 = response.json()
    assert profile1["id"]
    assert profile1["username"] == username
    assert profile1["email"] is None
    assert profile1["has_password"] == False

    # set email
    params = dict(email="test_email@test.ru")
    response = client.post("/v1/user/profile/email", headers=headers, json=params)
    assert response.status_code == 200

    # check profile
    response = client.get("/v1/user/profile", headers=headers)
    assert response.status_code == 200
    profile2 = response.json()
    assert profile2["id"] == profile1["id"]
    assert profile2["username"] == username
    assert profile2["email"] == params["email"]
    assert profile2["has_password"] == False
