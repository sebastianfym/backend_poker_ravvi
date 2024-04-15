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


def test_member_in_club(api_client: TestClient, api_guest: UserAccessProfile, api_client_2: TestClient,
                     api_guest_2: UserAccessProfile):
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}
    api_client_2.headers = {"Authorization": "Bearer " + api_guest_2.access_token}

    ascii_letters = list(string.ascii_letters)
    digits = list(string.digits)

    club_name = ""

    for i in range(10):
        club_name_letter = random.choice(ascii_letters)
        club_name_number = random.choice(digits)
        club_name += club_name_letter + str(club_name_number)

    club_name_2 = club_name[-1::-1]

    # create club without props (defaults)
    params = {}
    response = api_client.post("/api/v1/clubs", json=params)
    assert response.status_code == 201

    club1 = ClubProfile(**response.json())

    request = api_client.get(f"/api/v1/clubs/{club1.id}/members")
    assert request.status_code == 200

    request = api_client.get(f"/api/v1/clubs/{87654}/members")
    assert request.status_code == 404

    request = api_client_2.post(f"/api/v1/clubs/{club1.id}/members", json={})
    assert request.status_code == 200

    request = api_client_2.get(f"/api/v1/clubs/{club1.id}/members")
    assert request.status_code == 403

    # params = {"name": club_name_2, "description": "Some new desc", "automatic_confirmation": True}
    # response = api_client.patch(f"/api/v1/clubs/{club1.id}", json=params)
    # assert response.status_code == 200



