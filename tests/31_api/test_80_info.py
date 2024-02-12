import logging
import os

import pytest
from fastapi.testclient import TestClient
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_401_UNAUTHORIZED
from ravvi_poker.api.auth import UserAccessProfile

from ravvi_poker.engine import data

logger = logging.getLogger(__name__)


def test_get_levels_schedule_no_access(api_client: TestClient, api_guest: UserAccessProfile):
    # negative (no access)
    response = api_client.get(f"/v1/info/levels_schedule/unknown")
    assert response.status_code == HTTP_401_UNAUTHORIZED


def test_get_levels_schedule(api_client: TestClient, api_guest: UserAccessProfile):
    # set headers
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}

    # negative (not found)
    response = api_client.get(f"/v1/info/levels_schedule/unknown")
    assert response.status_code == HTTP_404_NOT_FOUND

    # positive
    table_type = {
        "sng": ["standard", "turbo"],
        "mtt": ["standard", "turbo", "hyperturbo"]
    }

    for table_type, schedules in table_type.items():
        for schedule_type in schedules:
            logger.info("%s/%s", table_type, schedule_type)
            response = api_client.get(f"/v1/info/levels_schedule/{table_type}")
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

    response = api_client.get("/v1/info/countries/ru/")
    assert response.status_code == 200

    response = api_client.get("/v1/info/countries/tg/")
    assert response.status_code == 400

    response = api_client.get("/v1/info/countries/ru/")
    assert list(response.json().values())[0] == "Абхазия"

    response = api_client.get("/v1/info/countries/en/")
    assert list(response.json().values())[0] == "Abkhazia"


def test_rewards_distribution(api_client: TestClient, api_guest: UserAccessProfile):

    response = api_client.get("/v1/info/rewards_distribution")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}
    response = api_client.get("/v1/info/rewards_distribution")
    assert response.status_code == 200

# def test_timezone(api_client: TestClient, api_guest: UserAccessProfile):
#     api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}
#
#     response = api_client.get("/v1/info/timezone")
#     assert response.status_code == 200
#     assert isinstance(response.json(), list)
#     assert response.json()[0] == "Africa/Abidjan"
#
#     response_2 = api_client.post("/v1/info/timezone", json={"timezone_user": "America/Atka"})
#     assert response_2.status_code == 200
#     assert response_2.json() == "-10:0"
#
#     response_2 = api_client.post("/v1/info/timezone", json={})
#     assert response_2.status_code == 422

