from fastapi.testclient import TestClient

from ravvi_poker_backend.api.main import app

client = TestClient(app)


def register_guest():
    response = client.post("/v1/auth/register", json={})
    assert response.status_code == 200
    result = response.json()
    username = result["username"]
    access_token = result["access_token"]
    return access_token, username


def test_20_clubs():
    # register new guest
    access_token, username = register_guest()
    headers = {"Authorization": "Bearer " + access_token}

    # create club
    params = dict(name="test_20_A")
    response = client.post("/v1/clubs", headers=headers, json=params)
    assert response.status_code == 200
    club1 = response.json()
    assert club1["id"]
    assert club1["name"] == "test_20_A"

    # create club
    params = dict(name="test_20_B")
    response = client.post("/v1/clubs", headers=headers, json=params)
    assert response.status_code == 200
    club2 = response.json()
    assert club2["id"]
    assert club2["name"] == "test_20_B"

    # list clubs
    response = client.get("/v1/clubs", headers=headers)
    assert response.status_code == 200
    clubs = response.json()
    assert isinstance(clubs, list)
    clubs.sort(key=lambda x: x['name'])
    club_A = clubs[0]
    assert club_A['name'] == "test_20_A"
    assert club_A['user_role'] == "OWNER"
    club_B = clubs[1]
    assert club_B['name'] == "test_20_B"
    assert club_B['user_role'] == "OWNER"

    # get club
    response = client.get(f"/v1/clubs/{club1['id']}", headers=headers)
    assert response.status_code == 200
    club_A_v1 = response.json()
    assert club_A_v1["name"] == "test_20_A"

    # update club
    params = dict(name="test_20_C")
    response = client.put(f"/v1/clubs/{club2['id']}", headers=headers, json=params)
    assert response.status_code == 200
    club_B_v2 = response.json()
    assert club_B_v2["name"] == "test_20_C"

