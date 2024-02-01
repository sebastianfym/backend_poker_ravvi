import json

import pytest

from starlette.status import HTTP_400_BAD_REQUEST, HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN, \
    HTTP_422_UNPROCESSABLE_ENTITY, HTTP_418_IM_A_TEAPOT
from fastapi.testclient import TestClient
from ravvi_poker.api.auth import UserAccessProfile
from ravvi_poker.api.clubs import ClubProfile, ClubMemberProfile


def test_create_club(api_client: TestClient, api_guest: UserAccessProfile, api_client_2: TestClient,
                     api_guest_2: UserAccessProfile):
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
    # assert club1["id"] in my_clubs_ids
    # assert club2["id"] in my_clubs_ids

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
    # response = client.delete(f"/v1/clubs/{club2['id']}", headers=new_headers)
    # assert response.status_code == 403

    # delete club2 by user
    # response = client.delete(f"/v1/clubs/{club2['id']}", headers=headers)
    # assert response.status_code == 204

    # create and get clubs tables

    params = {
        "table_name": "TEST",
        "table_type": "RG",
        "table_seats": 6,
        "game_type": "NLH",
        "game_subtype": "REGULAR"
    }
    response = api_client.post(f"/v1/clubs/{club1.id}/tables", json=params)
    assert response.status_code == 201

    response = api_client.get(f"/v1/clubs/{club1.id}/tables")
    assert response.status_code == 200
    assert isinstance(response.json(), list) is True
    assert response.json() != []


def test_21_club_join(api_client: TestClient, api_guest: UserAccessProfile, api_client_2: TestClient,
                      api_guest_2: UserAccessProfile):
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

    # response = api_client_2.get("/v1/clubs")
    # assert response.status_code == 200
    # clubs = response.json()
    # assert clubs

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

    response = api_client.post(
        f"/v1/clubs/{23131232141241212512512125125551525252152151251252151554554765634353534534}/members")
    assert response.status_code == 404
    assert response.json() == {"detail": "Club not found"}

    response = api_client.post(
        f"/v1/clubs/{23131232141241212512512125125551525252152151251252151554554765634353534534}/members")
    assert response.status_code == 404
    assert response.json() == {"detail": "Club not found"}

    response = api_client.put(
        f"/v1/clubs/{23131232141241212512512125125551525252152151251252151554554765634353534534}/members/{p.id}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Club not found"}

    response = api_client.put(f"/v1/clubs/{club.id}/members/{1231242521215253634645748567856345235252362346354747544}")
    assert response.status_code == 404
    assert response.json() == {'detail': 'Member not found'}


def test_get_relations(api_client: TestClient, api_guest: UserAccessProfile):
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}

    params = {}
    response = api_client.post("/v1/clubs", json=params)
    assert response.status_code == 201

    club = ClubProfile(**response.json())
    response = api_client.get(f'/v1/clubs/{club.id}/relation_clubs')
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    response = api_client.get(f"/v1/clubs/{club.id}/relation_union")
    assert response.status_code == 404
    assert response.json() == {'detail': 'Union not found'}


def test_get_club(api_client: TestClient, api_guest: UserAccessProfile):
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}

    # create club without props (defaults)
    params = {}
    response = api_client.post("/v1/clubs", json=params)
    assert response.status_code == 201

    club = ClubProfile(**response.json())
    assert club.id
    assert club.user_role == "O"

    response = api_client.get("/v1/clubs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json()[0]['user_balance'] == 0.0
    assert response.json()[0]['agents_balance'] == 0.0
    assert response.json()[0]['club_balance'] == 0.0
    assert response.json()[0]['service_balance'] == 0.0

    club.user_role = 'P'
    assert club.club_balance is None
    assert club.service_balance is None
    assert club.agents_balance is None


def test_txn_balance_club(api_client: TestClient, api_guest: UserAccessProfile, api_client_2: TestClient,
                      api_guest_2: UserAccessProfile):
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}
    api_client_2.headers = {"Authorization": "Bearer " + api_guest_2.access_token}

    params = {}
    response = api_client.post("/v1/clubs", json=params)
    assert response.status_code == 201

    club = ClubProfile(**response.json())

    #Actions with manipulations of the club's balance

    response = api_client.post(f"/v1/clubs/{club.id}/add_chip_on_club_balance", json={})
    assert response.status_code == 200
    assert response.json()['status_code'] == 400
    assert response.json()['detail'] == 'You forgot to amount out quantity the chips'

    response = api_client.post(f"/v1/clubs/{club.id}/add_chip_on_club_balance", json={"amount": 1000})
    assert response.status_code == 200
    response = api_client.get(f"/v1/clubs/{club.id}")
    assert response.json()['club_balance'] == 1000
    assert response.status_code == 200

    response = api_client.post(f"/v1/clubs/{club.id}/add_chip_on_club_balance", json={})
    assert response.status_code == 200
    assert response.json()['status_code'] == 400
    assert response.json()['detail'] == 'You forgot to amount out quantity the chips'

    response = api_client.post(f"/v1/clubs/{club.id}/delete_chip_from_club_balance", json={})
    assert response.status_code == 200
    assert response.json()['status_code'] == 400
    assert response.json()['detail'] == 'You forgot to amount out quantity the chips'

    response = api_client.post(f"/v1/clubs/{club.id}/delete_chip_from_club_balance", json={"amount": 1})
    assert response.status_code == 200
    response = api_client.get(f"/v1/clubs/{club.id}")
    assert response.status_code == 200
    assert response.json()['club_balance'] == 999

    response = api_client_2.post(f"/v1/clubs/{club.id}/delete_chip_from_club_balance", json={"amount": 1})
    assert response.json()['status_code'] == 403

    response = api_client_2.post(f"/v1/clubs/{club.id}/add_chip_on_club_balance", json={"amount": 1})
    assert response.json()['status_code'] == 403

    #Action with manipulations of the club's user balance

    response = api_client.post(f"/v1/clubs/{club.id}/giving_chips_to_the_user", json={"amount": 1, "user_id": 1, "balance": "user_balance"})
    assert response.json() == 418

    response = api_client.post(f"/v1/clubs/{club.id}/giving_chips_to_the_user", json={"amount": 1})
    assert response.json()['status_code'] == 400
    assert response.json()['detail'] == "You forgot to add a value: 'user_id'"

    response = api_client.post(f"/v1/clubs/{club.id}/giving_chips_to_the_user", json={"user_id": 1})
    assert response.json()['status_code'] == 400
    assert response.json()['detail'] == "You forgot to add a value: 'amount'"

    response = api_client.post(f"/v1/clubs/{club.id}/giving_chips_to_the_user", json={"amount": 1, "user_id": 1})
    assert response.json()['status_code'] == 400
    assert response.json()['detail'] == "You forgot to add a value: 'balance'"

    response = api_client_2.post(f"/v1/clubs/{club.id}/giving_chips_to_the_user", json={"amount": 1, "user_id": 1, "balance": "user_balance"})
    assert response.json()['status_code'] == 403
    assert response.json()['detail'] == "You don't have enough rights to perform this action"

    response = api_client.post(f"/v1/clubs/{club.id}/delete_chips_from_the_user", json={"amount": 1, "user_id": 1, "balance": "user_balance"})
    assert response.json() == 418

    response = api_client.post(f"/v1/clubs/{club.id}/delete_chips_from_the_user", json={"amount": 1})
    assert response.json()['status_code'] == 400
    assert response.json()['detail'] == "You forgot to add a value: 'user_id'"

    response = api_client.post(f"/v1/clubs/{club.id}/delete_chips_from_the_user", json={"user_id": 1})
    assert response.json()['status_code'] == 400
    assert response.json()['detail'] == "You forgot to add a value: 'amount'"

    response = api_client.post(f"/v1/clubs/{club.id}/delete_chips_from_the_user", json={"amount": 1, "user_id": 1})
    assert response.json()['status_code'] == 400
    assert response.json()['detail'] == "You forgot to add a value: 'balance'"

    response = api_client_2.post(f"/v1/clubs/{club.id}/delete_chips_from_the_user", json={"amount": 1, "user_id": 1, "balance": "user_balance"})
    assert response.json()['status_code'] == 403
    assert response.json()['detail'] == "You don't have enough rights to perform this action"

    #The user requests chips from the club

    response = api_client.post(f"/v1/clubs/{club.id}/request_chips", json={"amount": 1, "balance": "balance_shared"})
    assert response.status_code == 200

    response = api_client.post(f"/v1/clubs/{club.id}/request_chips", json={"amount": 1})
    assert response.json()['status_code'] == 400
    assert response.json()['detail'] == "You forgot to add a value: 'balance'"

    response = api_client.post(f"/v1/clubs/{club.id}/request_chips", json={"balance": "balance_shared"})
    assert response.json()['status_code'] == 400
    assert response.json()['detail'] == "You forgot to add a value: 'amount'"

    response = api_client_2.post(f"/v1/clubs/{club.id}/request_chips", json={"amount": 1, "balance": "balance_shared"})
    assert response.json()['status_code'] == 403
    assert response.json()['detail'] == "You don't have enough rights to perform this action"