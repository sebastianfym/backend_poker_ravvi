import json
import random
import string
from decimal import Decimal
from time import monotonic

import pytest

from fastapi.testclient import TestClient
from ravvi_poker.api.auth.types import UserAccessProfile
from ravvi_poker.api.clubs.types import ClubProfile, ClubMemberProfile
from ravvi_poker.db import DBI


def test_members_request_club(api_client: TestClient, api_guest: UserAccessProfile, api_client_2: TestClient,
                     api_guest_2: UserAccessProfile):
    # set headers
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}
    api_client_2.headers = {"Authorization": "Bearer " + api_guest_2.access_token}

    ascii_letters = list(string.ascii_letters)
    digits = list(string.digits)

    club_name = ""

    for i in range(10):
        club_name_letter = random.choice(ascii_letters)
        club_name_number = random.choice(digits)
        club_name += club_name_letter + str(club_name_number)


    params = {}
    request = api_client.post("/api/v1/clubs", json=params)
    assert request.status_code == 201

    club1 = ClubProfile(**request.json())

    request = api_client.post(f"/api/v1/clubs/{club1.id}/chips", json={"action": "IN", "amount": 500000})

    request = api_client_2.post(f"/api/v1/clubs/{404}/chips/requests", json={"amount": 100, "agent": False})
    assert request.status_code == 404

    request = api_client_2.post(f"/api/v1/clubs/{club1.id}/chips/requests", json={"amount": 100, "agent": False})
    assert request.status_code == 404
    assert request.json()['detail'] == "Member not found"

    request = api_client_2.post(f"/api/v1/clubs/{club1.id}/members", json={})
    assert request.status_code == 200

    request = api_client_2.post(f"/api/v1/clubs/{club1.id}/chips/requests", json={"amount": 100, "agent": False})
    assert request.status_code == 403

    response = api_client.get(f"/api/v1/clubs/{club1.id}/members/requests")
    assert response.status_code == 200

    request = api_client.get(f"/api/v1/clubs/{club1.id}/members/requests")
    assert request.status_code == 200

    user_2_id = int(request.json()[0].get('id'))

    data = {
        "rakeback": None,
        "agent_id": None,
        "nickname": None,
        "comment": None,
        "user_role": "S"
    }
    request = api_client.put(f"/api/v1/clubs/{club1.id}/members/{user_2_id}", json=data)
    assert request.status_code == 200

    request = api_client_2.post(f"/api/v1/clubs/{club1.id}/chips/requests", json={"amount": 100, "agent": False})
    assert request.status_code == 201

    request = api_client.get(f"/api/v1/clubs/{club1.id}/chips/requests")
    member_user_id = request.json()['users_requests'][0]['id']
    txn_id = request.json()['users_requests'][0]['txn_id']
    assert request.status_code == 200

    request = api_client.put(f"/api/v1/clubs/{club1.id}/chips/requests/{txn_id}", json={"action": "approve"})
    assert request.status_code == 200

    request = api_client.post(f"/api/v1/clubs/{club1.id}/chips/players/{member_user_id}", json={"action": "IN", "amount": 200})
    assert request.status_code == 201

    request = api_client_2.post(f"/api/v1/clubs/{club1.id}/chips/requests", json={"amount": 100, "agent": False})
    assert request.status_code == 201

    request = api_client_2.post(f"/api/v1/clubs/{club1.id}/chips/requests", json={"amount": 100, "agent": False})
    assert request.status_code == 400

    request = api_client.post(f"/api/v1/clubs/{club1.id}/chips/requests/all", json={"operation": "approve"})
    assert request.status_code == 200

    request = api_client.post(f"/api/v1/clubs/{club1.id}/chips/requests/all", json={"operation": "approve"})
    assert request.status_code == 200

    request = api_client_2.post(f"/api/v1/clubs/{club1.id}/chips/requests", json={"amount": 100, "agent": False})
    assert request.status_code == 201

    request = api_client.post(f"/api/v1/clubs/{club1.id}/chips/requests/all", json={"operation": "reject"})
    assert request.status_code == 200
