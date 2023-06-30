import json
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
    assert profile1["has_password"] is False

    # set password
    params = dict(new_password="test")
    response = client.post("/v1/auth/password", headers=headers, json=params)
    assert response.status_code == 200

    # check profile
    response = client.get("/v1/user/profile", headers=headers)
    assert response.status_code == 200

    profile2 = response.json()
    assert profile2["id"] == profile1["id"]
    assert profile2["username"] == profile1["username"]
    assert profile2["email"] is None
    assert profile2["has_password"] is True


# TODO проверить работу с передачей upload_path в photo
def test_update_user_profile():
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
    assert profile1["has_password"] is False
    assert profile1["photo"] is None

    # update username
    params = dict(username="test_username")
    response = client.patch("/v1/user/profile", headers=headers, json=params)
    assert response.status_code == 200

    # check profile
    response = client.get("/v1/user/profile", headers=headers)
    assert response.status_code == 200

    profile2 = response.json()
    assert profile2["id"] == profile1["id"]
    assert profile2["username"] == params["username"]
    assert profile2["email"] is None
    assert profile2["has_password"] is False
    assert profile1["photo"] is None

    # update photo
    params = dict(photo="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=")
    response = client.patch("/v1/user/profile", headers=headers, json=params)
    assert response.status_code == 200

    # check profile
    response = client.get("/v1/user/profile", headers=headers)
    assert response.status_code == 200

    profile3 = response.json()
    assert profile3["id"] == profile2["id"]
    assert profile3["username"] == profile2["username"]
    assert profile3["email"] is None
    assert profile3["has_password"] is False
    assert profile3["photo"] == params["photo"]

    # update_all_fields
    params = dict(
        username="final_test_username",
        photo="iVBORw0KGgoAAAANSUhEUgAAAAgAAAAIAQMAAAD+wSzIAAAABlBMVEX///+/v7+jQ3Y5AAAADklEQVQI12P4AIX8EAgALgAD/aNpbtEAAAAASUVORK5CYII=",
    )
    response = client.patch("/v1/user/profile", headers=headers, json=params)
    assert response.status_code == 200

    # check profile
    response = client.get("/v1/user/profile", headers=headers)
    assert response.status_code == 200

    profile4 = response.json()
    assert profile4["id"] == profile3["id"]
    assert profile4["username"] == params["username"]
    assert profile4["email"] is None
    assert profile4["has_password"] is False
    assert profile4["photo"] == params["photo"]


def test_set_user_email():
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
    assert profile1["has_password"] is False

    # set email
    params = dict(email="test_email@test.ru")
    response = client.post("/v1/user/profile/email", headers=headers, json=params)
    assert response.status_code == 200

    # check profile
    response = client.get("/v1/user/profile", headers=headers)
    assert response.status_code == 200

    profile2 = response.json()
    assert profile2["id"] == profile1["id"]
    assert profile2["username"] == profile1["username"]
    assert profile2["email"] == params["email"]
    assert profile2["has_password"] is False


def test_deactivate_user():
    # register new guest
    response = client.post("/v1/auth/register", json={})
    assert response.status_code == 200
    profile = response.json()
    device_token = profile["device_token"]
    user_id = profile["user_id"]
    username = profile["username"]

    # login via device_token
    params = {"device_token": device_token}
    response = client.post("/v1/auth/device", json=params)
    assert response.status_code == 200

    # check user
    profile1 = response.json()
    assert profile1["device_token"] == device_token
    assert profile1["user_id"] == user_id
    assert profile1["username"] == username

    # set user password
    access_token = profile1["access_token"]
    user_password = "test1234"
    params = {"new_password": user_password}
    headers = {"Authorization": "Bearer " + access_token}
    response = client.post("/v1/auth/password", json=params, headers=headers)
    assert response.status_code == 200

    # check user password
    headers = {"Authorization": "Bearer " + access_token}
    response = client.get("/v1/user/profile", headers=headers)
    profile2 = response.json()
    assert profile2["id"] == profile1["user_id"]
    assert profile2["username"] == profile1["username"]
    assert profile2["has_password"] is True

    # login via username and password
    params = {"username": username, "password": user_password}
    response = client.post("/v1/auth/login", data=params)
    assert response.status_code == 200

    # check user
    profile3 = response.json()
    assert profile3["user_id"] == profile2["id"]
    assert profile3["username"] == profile2["username"]

    # deactivate user
    access_token = profile3["access_token"]
    headers = {"Authorization": "Bearer " + access_token}
    response = client.delete("/v1/user/profile", headers=headers)
    assert response.status_code == 204

    # login via device_token
    device_token = profile3["device_token"]
    params = {"device_token": device_token}
    response = client.post("/v1/auth/device", json=params)
    assert response.status_code == 403

    # login via old device_token
    device_token = profile1["device_token"]
    params = {"device_token": device_token}
    response = client.post("/v1/auth/device", json=params)
    assert response.status_code == 403

    # login via username and password
    params = {"username": username, "password": user_password}
    response = client.post("/v1/auth/login", data=params)
    assert response.status_code == 403
