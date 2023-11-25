import pytest
pytestmark = pytest. mark. skip()

from fastapi.testclient import TestClient

from ravvi_poker.api.app import app

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

    # create club without props
    json = {}
    headers = {"Authorization": "Bearer " + access_token}
    response = client.post("/v1/clubs", json=json, headers=headers)
    assert response.status_code == 201

    # check club
    club1 = response.json()
    assert club1["id"]
    assert club1["name"].startswith("Club_")
    assert club1["description"] is None
    assert club1["image_id"] is None
    assert club1["user_role"] == "OWNER"
    assert club1["user_approved"] is True

    # create club with props
    json = {"name": "New club", "description": "Desc"}
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

    # update club2
    json = {"name": "Some new name", "description": "Some new desc"}
    response = client.patch(f"/v1/clubs/{club2['id']}", json=json, headers=headers)
    assert response.status_code == 200

    club2 = response.json()
    assert club2["id"]
    assert club2["name"] == json["name"]
    assert club2["description"] == json["description"]
    assert club2["image_id"] is None
    assert club2["user_role"] == "OWNER"
    assert club2["user_approved"] is True

    # register new user
    new_access_token, _ = register_guest()

    # get club2 by new user
    new_headers = {"Authorization": "Bearer " + new_access_token}
    response = client.get(f"/v1/clubs/{club2['id']}", headers=new_headers)
    assert response.status_code == 200

    club2 = response.json()
    assert club2["id"]
    assert club2["name"] == json["name"]
    assert club2["description"] == json["description"]
    assert club2["image_id"] is None
    assert club2["user_role"] is None
    assert club2["user_approved"] is None

    # update club2 by new user
    json = {"name": "User 2 new name"}
    response = client.patch(f"/v1/clubs/{club2['id']}", json=json, headers=new_headers)
    assert response.status_code == 403

    # delete club2 by new user
    response = client.delete(f"/v1/clubs/{club2['id']}", headers=new_headers)
    assert response.status_code == 403

    # delete club2 by user
    response = client.delete(f"/v1/clubs/{club2['id']}", headers=headers)
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
    assert club['user_approved'] is True

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
    assert result['user_approved'] is False

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
    assert club_A['user_approved'] is False

    # list memebers
    response = client.get(f"/v1/clubs/{club_id}/members", headers=headers_player)
    assert response.status_code == 200
    members = response.json()
    
    assert isinstance(members, list)
    assert len(members)==2
    clubs.sort(key=lambda x: x['id'])
    owner = members[0]
    #assert owner['username'] == owner_username
    assert owner['user_role'] == "OWNER"
    assert owner['user_approved'] is True

    player = members[1]
    #assert player['username'] == player_username
    assert player['user_role'] == "PLAYER"
    assert player['user_approved'] is False

    # approve join request
    response = client.post(f"/v1/clubs/{club_id}/members/{player['id']}", headers=headers_owner)
    assert response.status_code == 200

    member = response.json()
    assert member["user_approved"] is True

    # list members
    response = client.get(f"/v1/clubs/{club_id}/members", headers=headers_player)
    assert response.status_code == 200

    members = response.json()
    clubs.sort(key=lambda x: x['id'])
    player = members[1]

    assert player["user_approved"] is True

    # delete member
    response = client.delete(f"/v1/clubs/{club_id}/members/{player['id']}", headers=headers_owner)
    assert response.status_code == 204

# update club
# delete club
