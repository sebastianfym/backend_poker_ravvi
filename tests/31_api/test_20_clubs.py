import pytest

from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN, HTTP_422_UNPROCESSABLE_ENTITY
from fastapi.testclient import TestClient
from ravvi_poker.api.auth import UserAccessProfile
from ravvi_poker.api.clubs import ClubProfile, ClubMemberProfile


def test_create_club(api_client: TestClient, api_guest: UserAccessProfile, api_client_2: TestClient, api_guest_2: UserAccessProfile):

    club_404 = 4040404040
    # set headers
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}
    api_client_2.headers = {"Authorization": "Bearer " + api_guest_2.access_token}

    # create club without props (defaults)
    params = {}
    response = api_client.post("/v1/clubs", json=params)
    assert response.status_code == 201

    club1 = ClubProfile(**response.json())
    assert club1.id
    assert club1.name.startswith("CLUB-")
    assert club1.description is None
    assert club1.image_id is None
    assert club1.user_role == "O"
    assert club1.user_approved is True

    # create club with props
    params = {"name": "New club", "description": "Desc"}
    response = api_client.post("/v1/clubs", json=params)
    assert response.status_code == 201

    club2 = ClubProfile(**response.json())
    assert club2.id
    assert club2.name == "New club"
    assert club2.description == "Desc"
    assert club2.image_id is None
    assert club2.user_role == "O"
    assert club2.user_approved is True

    # get my clubs
    response = api_client.get("/v1/clubs")
    assert response.status_code == 200

    # check my clubs
    my_clubs = list(map(lambda x: ClubProfile(**x), response.json()))
    assert len(my_clubs) == 2
    #assert club1["id"] in my_clubs_ids
    #assert club2["id"] in my_clubs_ids

    # update club2
    params = {"name": "Some new name", "description": "Some new desc"}
    response = api_client.patch(f"/v1/clubs/{club2.id}", json=params)
    assert response.status_code == 200

    club2 = ClubProfile(**response.json())
    assert club2.id
    assert club2.name == "Some new name"
    assert club2.description == "Some new desc"
    assert club2.image_id is None
    assert club2.user_role == "O"
    assert club2.user_approved is True

    # get club2 by new user
    response = api_client_2.get(f"/v1/clubs/{club2.id}")
    assert response.status_code == 200
    club2_2 = ClubProfile(**response.json())
    assert club2_2.id == club2.id
    assert club2_2.user_role is None
    assert club2_2.user_approved is None

    response = api_client_2.get(f"/v1/clubs/{club_404}")
    assert response.status_code == 404

    # update club2 by new user
    params = {"name": "User 2 new name"}
    response = api_client_2.patch(f"/v1/clubs/{club2.id}", json=params)
    assert response.status_code == 403

    response = api_client_2.patch(f"/v1/clubs/{club_404}", json=params)
    assert response.status_code == 404

    # delete club2 by new user
    #response = client.delete(f"/v1/clubs/{club2['id']}", headers=new_headers)
    #assert response.status_code == 403

    # delete club2 by user
    #response = client.delete(f"/v1/clubs/{club2['id']}", headers=headers)
    #assert response.status_code == 204


def test_21_club_join(api_client: TestClient, api_guest: UserAccessProfile, api_client_2: TestClient, api_guest_2: UserAccessProfile):
    # set headers
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}
    api_client_2.headers = {"Authorization": "Bearer " + api_guest_2.access_token}

    # create club without props (defaults)
    response = api_client.post("/v1/clubs", json={})
    assert response.status_code == 201
    club = ClubProfile(**response.json())

    response = api_client_2.post(f"/v1/clubs/{club.id}/members")
    assert response.status_code == 200
    club_2 = ClubProfile(**response.json())
    assert club_2.id
    assert club_2.name
    assert club_2.user_role == 'P'
    assert club_2.user_approved is False

    # list clubs
    response = api_client.get("/v1/clubs")
    assert response.status_code == 200
    clubs = response.json()
    assert clubs

    response = api_client_2.get("/v1/clubs")
    assert response.status_code == 200
    clubs = response.json()
    assert clubs

    # list members
    response = api_client.get(f"/v1/clubs/{club.id}/members")
    assert response.status_code == 200
    members = [ClubMemberProfile(**m) for m in response.json()]
    pending = [m for m in members if not m.user_approved]
    assert members
    assert pending and len(pending) == 1

    # approve
    p = pending[0]
    response = api_client.put(f"/v1/clubs/{club.id}/members/{p.id}")
    assert response.status_code == 200
    member = ClubMemberProfile(**response.json())
    assert member.user_approved
