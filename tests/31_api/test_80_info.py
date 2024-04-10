import datetime
import json
import logging
import os

import pytest
from fastapi.testclient import TestClient
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_401_UNAUTHORIZED
from ravvi_poker.api.auth.types import UserAccessProfile
from ravvi_poker.api.clubs.types import ClubProfile
from ravvi_poker.db import DBI

from ravvi_poker.engine import data

logger = logging.getLogger(__name__)

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

def test_get_levels_schedule_no_access(api_client: TestClient, api_guest: UserAccessProfile):
    # negative (no access)
    response = api_client.get(f"/api/v1/info/levels_schedule/unknown")
    assert response.status_code == HTTP_401_UNAUTHORIZED


def test_get_levels_schedule(api_client: TestClient, api_guest: UserAccessProfile):
    # set headers
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}

    # negative (not found)
    response = api_client.get(f"/api/v1/info/levels_schedule/unknown")
    assert response.status_code == HTTP_404_NOT_FOUND

    # positive
    table_type = {
        "sng": ["standard", "turbo"],
        "mtt": ["standard", "turbo", "hyperturbo"]
    }

    for table_type, schedules in table_type.items():
        for schedule_type in schedules:
            logger.info("%s/%s", table_type, schedule_type)
            response = api_client.get(f"/api/v1/info/levels_schedule/{table_type}")
            assert response.status_code == HTTP_200_OK
            data = response.json()
            print(data)
            assert isinstance(data, dict)
            row = data['standard']
            assert isinstance(row, list)


# def test_get_payment_structure(api_client: TestClient, api_guest: UserAccessProfile):
#     # set headers
#     api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}

#     payment_structure_list = [
#         {"players": "1-3", "position": {"first": "100%", "second": "0", "third": "0"}},
#         {"players": "4-6", "position": {"first": "70%", "second": "30%", "third": "0"}},
#         {"players": "7-9", "position": {"first": "50%", "second": "30%", "third": "20%"}}
#     ]

#     response = api_client.get(f"/v1/info/payment structure")
#     assert response.status_code == 200
#     assert isinstance(response.json(), list)
#     assert response.json() == payment_structure_list

def test_countries_list(api_client: TestClient, api_guest: UserAccessProfile):
    data.getJSONFiles()

    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}

    response = api_client.get("/api/v1/info/countries/ru/")
    assert response.status_code == 200

    response = api_client.get("/api/v1/info/countries/tg/")
    assert response.status_code == 200

    response = api_client.get("/api/v1/info/countries/ru/")
    assert list(response.json().values())[0] == "Абхазия"

    response = api_client.get("/api/v1/info/countries/en/")
    assert list(response.json().values())[0] == "Abkhazia"


def test_rewards_distribution(api_client: TestClient, api_guest: UserAccessProfile):
    response = api_client.get("/api/v1/info/rewards_distribution")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}
    response = api_client.get("/api/v1/info/rewards_distribution")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_clubs_history(api_client: TestClient, api_guest: UserAccessProfile):
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}
    club = create_club(api_client)
    response = api_client.get(f"/api/v1/info/{club.id}/history")
    assert response.status_code == 200

    response = api_client.get(f"/api/v1/clubs/{club.id}/members")
    assert response.status_code == 200

    owner_user_id = response.json()[0]["id"]

    async with DBI() as db:
        owner_account = await db.find_account(user_id=owner_user_id, club_id=club.id)
        props = json.dumps({'balance_type': 'balance'})
        current_time = datetime.datetime.now()
        sql = (
            "INSERT INTO user_account_txn (created_ts, account_id, txn_type, txn_value, total_balance, props, sender_id) "
            "VALUES (%s, %s, 'CASHIN', 250, 250, %s, %s)")
        await db.cursor().execute(sql, (current_time, owner_account.id, props, owner_account.user_id))

        replenishment_props = json.dumps({"status": "approve", "balance": "balance"})
        sql = (
            "INSERT INTO user_account_txn (created_ts, account_id, txn_type, txn_value, total_balance, props, sender_id) "
            "VALUES (%s, %s, 'REPLENISHMENT', 250, 0, %s, %s)")
        await db.cursor().execute(sql, (current_time, owner_account.id, replenishment_props, owner_account.user_id))

        replenishment_error_props = json.dumps({"status": "approve", "balance": "balance"})

        sql = (
            "INSERT INTO user_account_txn (created_ts, account_id, txn_type, txn_value, total_balance, props, sender_id) "
            "VALUES (%s, %s, 'REWARD', 250, 0, %s, %s)")
        await db.cursor().execute(sql, (current_time, owner_account.id, replenishment_error_props, owner_account.user_id))

        sql = (
            "INSERT INTO user_account_txn (created_ts, account_id, txn_type, txn_value, total_balance, props, sender_id) "
            "VALUES (%s, %s, 'CASHIN', 00.00, 00.00, %s, %s)")
        await db.cursor().execute(sql, (current_time, owner_account.id, props, owner_account.user_id))

    response = api_client.get(f"/api/v1/info/{club.id}/history")
    print(response.json())
    assert response.status_code == 200