import logging
from fastapi.testclient import TestClient
from starlette.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_401_UNAUTHORIZED
from ravvi_poker.api.auth import UserAccessProfile

logger = logging.getLogger(__name__)

def test_get_levels_schedule_no_access(api_client: TestClient, api_guest: UserAccessProfile):
    # negative (no access)
    response = api_client.get(f"/v1/info/levels_schedule/unknown/unknown")
    assert response.status_code == HTTP_401_UNAUTHORIZED


def test_get_levels_schedule(api_client: TestClient, api_guest: UserAccessProfile):
    # set headers
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}

    # negative (not found)
    response = api_client.get(f"/v1/info/levels_schedule/unknown/unknown")
    assert response.status_code == HTTP_404_NOT_FOUND

    # positive
    table_type = {
        "sng": ["standard", "turbo"],
        "mtt": ["standard", "turbo", "hyperturbo"]
    }

    for table_type, schedules in table_type.items():
        for schedule_type in schedules:
            logger.info("%s/%s", table_type, schedule_type)
            response = api_client.get(f"/v1/info/levels_schedule/{table_type}/{schedule_type}")
            assert response.status_code == HTTP_200_OK
            data = response.json()
            assert isinstance(data, list)
            row = data[0]
            assert 'level' in row
            assert 'blind_small' in row
            assert 'blind_big' in row
            assert 'ante' in row


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