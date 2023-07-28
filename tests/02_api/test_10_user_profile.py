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


def test_user_profile():
    # register user
    access_token, username = register_guest()

    # check user profile
    headers = {"Authorization": "Bearer " + access_token}
    response = client.get("/v1/user/profile", headers=headers)
    assert response.status_code == 200

    profile = response.json()
    assert profile["id"]
    assert profile["has_password"] is False
    assert profile["username"] == username
    assert profile["email"] is None
    assert profile["image_id"] is None

    # update username
    json_uname = {"username": f"test_username_{profile['id']}"}
    response = client.patch("/v1/user/profile", json=json_uname, headers=headers)
    assert response.status_code == 200

    # check user profile
    profile = response.json()
    assert profile["id"]
    assert profile["has_password"] is False
    assert profile["username"] == json_uname["username"]
    assert profile["email"] is None
    assert profile["image_id"] is None

    # register new user
    new_access_token, new_username = register_guest()

    # get user info by new user
    new_headers = {"Authorization": "Bearer " + new_access_token}
    response = client.get(f"/v1/user/{profile['id']}/profile", headers=new_headers)
    assert response.status_code == 200

    # check user profile by new user
    user_profile = response.json()
    assert user_profile["id"] == profile["id"]
    assert user_profile["username"] == profile["username"]
    assert user_profile["image_id"] == profile["image_id"]

    # try to set username by new user
    json = {"username": user_profile["username"]}
    response = client.patch("/v1/user/profile", json=json, headers=new_headers)
    assert response.status_code == 422

    # check new user profile
    response = client.get("/v1/user/profile", headers=new_headers)
    assert response.status_code == 200

    new_profile = response.json()
    assert new_profile["username"] == new_username


def test_set_email():
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

    # set user email
    json = {"email": "test1@mail.ru"}
    response = client.post("/v1/user/profile/email", json=json, headers=headers)
    assert response.status_code == 200

    temp_email1 = response.json()

    # check user profile
    response = client.get("/v1/user/profile", headers=headers)
    assert response.status_code == 200

    profile = response.json()
    assert profile["id"]
    assert profile["has_password"] is False
    assert profile["username"]
    assert profile["email"] is None
    assert profile["image_id"] is None

    # set new user email
    json = {"email": "test2@mail.ru"}
    response = client.post("/v1/user/profile/email", json=json, headers=headers)
    assert response.status_code == 200

    temp_email2 = response.json()

    # try to approve temp_email1
    response = client.post(f"/v1/user/profile/email/{temp_email1['uuid']}", headers=headers)
    assert response.status_code == 422

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

    # try to approve temp_email2
    response = client.post(f"/v1/user/profile/email/{temp_email2['uuid']}", headers=headers)
    assert response.status_code == 200

    # check user profile
    headers = {"Authorization": "Bearer " + access_token}
    response = client.get("/v1/user/profile", headers=headers)
    assert response.status_code == 200

    profile = response.json()
    assert profile["id"]
    assert profile["has_password"] is False
    assert profile["username"]
    assert profile["email"] == temp_email2["temp_email"]
    assert profile["image_id"] is None

    # try to approve temp_email2 again
    response = client.post(f"/v1/user/profile/email/{temp_email2['uuid']}", headers=headers)
    assert response.status_code == 422

    # try to set same email
    response = client.post("/v1/user/profile/email", json=json, headers=headers)
    assert response.status_code == 422
