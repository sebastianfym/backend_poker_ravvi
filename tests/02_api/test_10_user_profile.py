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


def test_get_user():
    # register user
    access_token, _ = register_guest()

    # check user profile
    headers = {"Authorization": "Bearer " + access_token}
    response = client.get("/v1/user/profile", headers=headers)
    assert response.status_code == 200

    profile = response.json()
    assert profile["id"]
    assert profile["has_password"] is False
    assert profile["username"]
    assert profile["email"] is None
    assert profile["image_id"] is None


def test_deactivate_user():
    # register user
    response = client.post("/v1/auth/register", json={})
    assert response.status_code == 200

    user = response.json()
    device_token = user["device_token"]
    access_token = user["access_token"]
    username = user["username"]

    # login via device_token
    json = {"device_token": device_token}
    response = client.post("/v1/auth/device", json=json)
    assert response.status_code == 200

    # set user password
    password = "testpswd1234"
    json = {"new_password": password}
    headers = {"Authorization": "Bearer " + access_token}
    response = client.post("/v1/auth/password", json=json, headers=headers)
    assert response.status_code == 200

    # login via username and password
    data = {"username": username, "password": password}
    response = client.post("/v1/auth/login", data=data)
    assert response.status_code == 200

    # deactivate user
    user = response.json()
    access_token = user["access_token"]
    headers = {"Authorization": "Bearer " + access_token}
    response = client.delete("/v1/user/profile", headers=headers)
    assert response.status_code == 204

    # login via device_token
    json = {"device_token": user["device_token"]}
    response = client.post("/v1/auth/device", json=json)
    assert response.status_code == 403

    # login via old device_token
    json = {"device_token": device_token}
    response = client.post("/v1/auth/device", json=json)
    assert response.status_code == 403

    # login via username and password
    data = {"username": username, "password": password}
    response = client.post("/v1/auth/login", data=data)
    assert response.status_code == 403


def test_set_user_username():
    # register guest
    access_token, _ = register_guest()

    # set username
    json = {"username": "test_username"}
    headers = {"Authorization": "Bearer " + access_token}
    response = client.patch("/v1/user/profile", json=json, headers=headers)
    assert response.status_code == 200

    # check username
    profile = response.json()
    assert profile["username"] == json["username"]

    # TODO add not unique logic


def test_set_user_email():
    # register guest
    access_token, _ = register_guest()

    # set email
    json = {"email": "email@test.ru"}
    headers = {"Authorization": "Bearer " + access_token}
    response = client.patch("/v1/user/profile", json=json, headers=headers)
    assert response.status_code == 200

    # check email 
    profile = response.json()
    assert profile["email"] == json["email"]

    # TODO ask questions about email logic


def test_patch_empty_user():
    # register user
    access_token, _ = register_guest()

    # set username and email
    json = {"username": "test_username", "email": "email@test.ru"}
    headers = {"Authorization": "Bearer " + access_token}
    response = client.patch("/v1/user/profile", json=json, headers=headers)
    assert response.status_code == 200

    # check user profile
    profile = response.json()
    assert profile["username"] == json["username"]
    assert profile["email"] == json["email"]

    # update user with no data
    json = {}
    response = client.patch("/v1/user/profile", json=json, headers=headers)
    assert response.status_code == 200

    # check user profile
    new_profile = response.json()
    assert new_profile["username"] == profile["username"]
    assert new_profile["email"] == profile["email"]


def test_get_user_info():
    # register user
    access_token, _ = register_guest()

    # register new user
    new_access_token, _ = register_guest()

    # get new user profile
    headers = {"Authorization": "Bearer " + new_access_token}
    response = client.get("/v1/user/profile", headers=headers)
    assert response.status_code == 200

    new_profile = response.json()
    new_profile_id = new_profile["id"]
    new_profile_username = new_profile["username"]
    new_profile_image_id = new_profile["image_id"]

    # get new user profile info by user
    headers = {"Authorization": "Bearer " + access_token}
    response = client.get(f"/v1/user/{new_profile_id}/profile", headers=headers)
    assert response.status_code == 200

    # check new profile info
    new_profile_info = response.json()
    assert new_profile_info["id"] == new_profile_id
    assert new_profile_info["username"] == new_profile_username
    assert new_profile_info["image_id"] == new_profile_image_id

    # get none user profile info
    none_user_id = new_profile_id + 100500
    response = client.get(f"/v1/user/{none_user_id}/profile", headers=headers)
    assert response.status_code == 404
