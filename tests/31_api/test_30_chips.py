import json
from decimal import Decimal

import pytest

from fastapi.testclient import TestClient
from ravvi_poker.api.auth import UserAccessProfile
from ravvi_poker.api.clubs import ClubProfile, ClubMemberProfile


@pytest.fixture
def client(request, api_client: TestClient, api_guest: UserAccessProfile,
           api_client_2: TestClient, api_guest_2: UserAccessProfile):
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}
    if request.__dict__["param"][0] == "get_authorize_client":
        api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}
        yield api_client
    elif request.__dict__["param"][0] == "get_two_clients":
        api_client_2.headers = {"Authorization": "Bearer " + api_guest_2.access_token}
        yield [api_client, api_client_2]


def create_club(client: list[TestClient] | TestClient):
    params = {}
    if isinstance(client, list):
        response = client[0].post("/api/v1/clubs", json=params)
    elif isinstance(client, TestClient):
        response = client.post("/api/v1/clubs", json=params)
    else:
        raise ValueError("incorrect client type")
    club = ClubProfile(**response.json())

    return club


# @pytest.mark.parametrize("client", [["get_two_clients", 100]], indirect=["client"])
def test_txns_in_club(api_client: TestClient, api_guest: UserAccessProfile, api_client_2: TestClient,
                            api_guest_2: UserAccessProfile):
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}
    api_client_2.headers = {"Authorization": "Bearer " + api_guest_2.access_token}

    # create club without props (defaults)
    params = {}
    response = api_client.post("/api/v1/clubs", json=params)
    assert response.status_code == 201

    club1 = ClubProfile(**response.json())
    assert club1.id
    assert club1.name.startswith("CLUB-")

    response = api_client_2.post(f"/api/v1/clubs/{club1.id}/members", json={})
    assert response.status_code == 200

    response = api_client.get(f"/api/v1/clubs/{club1.id}/members/requests")
    assert response.status_code == 200

    data = {
        "rakeback": 0,
        "agent_id": 0,
        "nickname": "string",
        "comment": "string",
        "user_role": "A"
    }
    response = api_client.put(f"/api/v1/clubs/{club1.id}/members/{response.json()[0]['id']}", json=data)
    assert response.status_code == 200

    response = api_client.get(f"/api/v1/clubs/{club1.id}/members")
    second_member_id = response.json()[1]['id']
    assert response.status_code == 200

    response = api_client.post(f"/api/v1/chips/{club1.id}/club/chips", json={"amount": 5000})
    assert response.status_code == 201

    response = api_client.post(f"/api/v1/chips/{club1.id}/club/chips", json={"amount": -50})
    assert response.status_code == 201

    response = api_client.get(f"/api/v1/clubs/{club1.id}")
    assert response.status_code == 200

    # response = api_client.delete(f"/api/v1/chips/{club1.id}/club/chips", data={"amount": 5000})
    # assert response.status_code == 200

    data = {
        "mode": "give_out",
        "amount": 500,
        "club_member": [
            {
                "id": second_member_id,
                "balance": 1000,
                "balance_shared": None
            },
        ]
    }
    response = api_client.post(f"/api/v1/chips/{club1.id}/players/chips", json=data)
    assert response.status_code == 201

    data = {
        "mode": "give_out",
        "amount": 100,
        "club_member": [
            {
                "id": second_member_id,
                "balance": 1000,
                "balance_shared": 1000
            },
        ]
    }
    response = api_client.post(f"/api/v1/chips/{club1.id}/players/chips", json=data)
    assert response.status_code == 201

    response = api_client.post(f"/api/v1/chips/{club1.id}/agents/chips/{second_member_id}",
                               json={"amount": 200, "mode": "give_out"})
    assert response.status_code == 201

    response = api_client.post(f"/api/v1/chips/{club1.id}/agents/chips/{second_member_id}",
                               json={"amount": 200, "mode": "pick_up"})
    assert response.status_code == 201

    data = {
      "amount": 200,
      "agent": True
    }
    response = api_client_2.post(f"/api/v1/chips/{club1.id}/requests/chips", json=data)
    assert response.status_code == 201

    response = api_client.get(f"/api/v1/chips/{club1.id}/requests/chips")
    assert response.status_code == 200

    response = api_client.put(f"/api/v1/chips/{club1.id}/requests/chips/{response.json()['users_requests'][0]['txn_id']}",
                              json={"action": "approve"})
    assert response.status_code == 200

    response = api_client_2.post(f"/api/v1/chips/{club1.id}/requests/chips", json=data)
    assert response.status_code == 201

    response = api_client.get(f"/api/v1/chips/{club1.id}/requests/chips")
    assert response.status_code == 200

    response = api_client.put(f"/api/v1/chips/{club1.id}/requests/chips/{response.json()['users_requests'][0]['txn_id']}",
                              json={"action": "reject"})
    assert response.status_code == 200

    data = {
        "amount": 200,
        "agent": True
    }
    response = api_client_2.post(f"/api/v1/chips/{club1.id}/requests/chips", json=data)
    assert response.status_code == 201

    response = api_client.get(f"/api/v1/chips/{club1.id}/requests/chips")
    assert response.status_code == 200

