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
    # register user
    access_token, _ = register_guest()

    # create club without any props
    json = {}
    headers = {"Authorization": "Bearer " + access_token}
    response = client.post("/v1/clubs", json=json, headers=headers)
    assert response.status_code == 201

    club1 = response.json()
    assert club1["id"]
    assert club1["name"]
    assert club1["description"] is None
    assert club1["image_id"] is None
    assert club1["user_role"] == "OWNER"
    assert club1["user_approved"] is True

    # get club
    response = client.get(f"/v1/clubs/{club1['id']}", headers=headers)
    assert response.status_code == 200

    club = response.json()
    assert club["id"] == club1["id"]
    assert club["name"] == club1["name"]
    assert club["description"] is None
    assert club["image_id"] is None
    assert club["user_role"] == club1["user_role"]
    assert club["user_approved"] == club1["user_approved"]

    # try to get non-existent club
    non_club_id = club1['id'] + 100500
    response = client.get(f"/v1/clubs/{non_club_id}", headers=headers)
    assert response.status_code == 404

    # create club with name and description
    json = {"name": "my club", "description": "description of my club"}
    response = client.post("/v1/clubs", json=json, headers=headers)
    assert response.status_code == 201

    club2 = response.json()
    assert club2["id"]
    assert club2["name"] == json["name"]
    assert club2["description"] == json["description"]
    assert club2["image_id"] is None
    assert club2["user_role"] == "OWNER"
    assert club2["user_approved"] is True

    # get my clubs
    response = client.get("/v1/clubs", headers=headers)
    assert response.status_code == 200

    # check my clubs
    my_clubs = response.json()
    my_clubs_ids = list(map(lambda x: x["id"], my_clubs))
    assert len(my_clubs) == 2
    assert club1["id"] in my_clubs_ids
    assert club2["id"] in my_clubs_ids

    # register new user
    new_access_token, _ = register_guest()

    # get club by new user
    new_headers = {"Authorization": "Bearer " + new_access_token}
    response = client.get(f"/v1/clubs/{club1['id']}", headers=new_headers)
    assert response.status_code == 200

    club = response.json()
    assert club["id"] == club1["id"]
    assert club["name"] == club1["name"]
    assert club["description"] is None
    assert club["image_id"] is None
    assert club["user_role"] is None
    assert club["user_approved"] is None

    # update club1
    json = {"name": "New name", "description": "New description"}
    response = client.patch(f"/v1/clubs/{club1['id']}", json=json, headers=headers)
    assert response.status_code == 200

    # check club1
    club = response.json()

    assert club["id"] == club1["id"]
    assert club["name"] == json["name"]
    assert club["description"] == json["description"]
    assert club["image_id"] is None
    assert club["user_role"] == club1["user_role"]
    assert club["user_approved"] == club1["user_approved"]

    # update club1 by new user
    json = {"name": "Impossible name", "description": "Impossible description"}
    response = client.patch(f"/v1/clubs/{club1['id']}", json=json, headers=new_headers)
    assert response.status_code == 403

    # delete club1
    response = client.delete(f"/v1/clubs/{club1['id']}", headers=headers)
    assert response.status_code == 204


def test_21_club_join():
    # register new guest - owner
    access_token, owner_username = register_guest()
    headers_owner = {"Authorization": "Bearer " + access_token}

    # create clubas owner
    params = dict(name="test_21")
    response = client.post("/v1/clubs", headers=headers_owner, json=params)
    assert response.status_code == 201
    club = response.json()
    assert club["id"]
    assert club["name"] == "test_21"
    assert club['user_role'] == "OWNER"
    assert club['user_approved'] == True

    club_id = club["id"]

    # register new guest - player
    access_token, player_username = register_guest()
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

    # list memebers
    response = client.get(f"/v1/clubs/{club_id}/members", headers=headers_player)
    assert response.status_code == 200
    members = response.json()
    
    assert isinstance(members, list)
    assert len(members)==2
    clubs.sort(key=lambda x: x['id'])
    owner = members[0]
    assert owner['username'] == owner_username
    assert owner['user_role'] == "OWNER"
    assert owner['user_approved'] == True

    player = members[1]
    assert player['username'] == player_username
    assert player['user_role'] == "PLAYER"
    assert player['user_approved'] == True
