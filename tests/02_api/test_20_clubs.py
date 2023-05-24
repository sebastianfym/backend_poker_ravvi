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
    assert club1["user_role"] == "OWNER"
    assert club1["user_approved"] == True

    # create club
    params = dict(name="test_20_B")
    response = client.post("/v1/clubs", headers=headers, json=params)
    assert response.status_code == 200
    club2 = response.json()
    assert club2["id"]
    assert club2["name"] == "test_20_B"
    assert club2["user_role"] == "OWNER"
    assert club2["user_approved"] == True

    # list clubs
    response = client.get("/v1/clubs", headers=headers)
    assert response.status_code == 200
    clubs = response.json()
    
    assert isinstance(clubs, list)
    assert len(clubs)==2
    clubs.sort(key=lambda x: x['name'])
    club_A = clubs[0]
    assert club_A['name'] == "test_20_A"
    assert club_A['user_role'] == "OWNER"
    assert club_A['user_approved'] == True
    club_B = clubs[1]
    assert club_B['name'] == "test_20_B"
    assert club_B['user_role'] == "OWNER"
    assert club_B['user_approved'] == True

    # get club
    response = client.get(f"/v1/clubs/{club1['id']}", headers=headers)
    assert response.status_code == 200
    club_A_v1 = response.json()
    assert club_A_v1["name"] == "test_20_A"
    assert club_A_v1['user_role'] == "OWNER"
    assert club_A_v1['user_approved'] == True

    # update club
    params = dict(name="test_20_C")
    response = client.put(f"/v1/clubs/{club2['id']}", headers=headers, json=params)
    assert response.status_code == 200
    club_B_v2 = response.json()
    assert club_B_v2["name"] == "test_20_C"
    assert club_B_v2['user_role'] == "OWNER"
    assert club_B_v2['user_approved'] == True


def test_21_club_join():
    # register new guest - owner
    access_token, username = register_guest()
    headers_owner = {"Authorization": "Bearer " + access_token}

    # create clubas owner
    params = dict(name="test_21")
    response = client.post("/v1/clubs", headers=headers_owner, json=params)
    assert response.status_code == 200
    club = response.json()
    assert club["id"]
    assert club["name"] == "test_21"
    assert club['user_role'] == "OWNER"
    assert club['user_approved'] == True

    club_id = club["id"]

    # register new guest - player
    access_token, username = register_guest()
    headers_player = {"Authorization": "Bearer " + access_token}


    response = client.post(f"/v1/clubs/{club_id}/members", headers=headers_player)
    assert response.status_code == 200
    result = response.json()
    assert result["id"]
    assert result["name"] == "test_21"
    assert result['user_role'] == "PLAYER"
    assert result['user_approved'] == True

    # list clubs
    response = client.get("/v1/clubs", headers=headers_player)
    assert response.status_code == 200
    clubs = response.json()
    
    assert isinstance(clubs, list)
    assert len(clubs)==1
    clubs.sort(key=lambda x: x['name'])
    club_A = clubs[0]
    assert club_A['name'] == "test_21"
    assert club_A['user_role'] == "PLAYER"
    assert club_A['user_approved'] == True
