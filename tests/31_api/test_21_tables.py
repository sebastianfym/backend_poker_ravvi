import pytest

from starlette.status import HTTP_200_OK, HTTP_201_CREATED
from fastapi.testclient import TestClient
from ravvi_poker.api.auth import UserAccessProfile
from ravvi_poker.api.clubs import ClubProfile, ClubMemberProfile
from ravvi_poker.api.tables import TableProfile

def test_create_table(api_client: TestClient, api_guest: UserAccessProfile):
    # set headers
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}

    # Создаем клуб
    # create club without props (defaults)
    params = {}
    response = api_client.post("/v1/clubs", json=params)
    assert response.status_code == 201
    club = ClubProfile(**response.json())

    # Создаем стол NLH
    params = {
        "table_name": "TEST",
        "table_type": "RG",
        "table_seats": 6,
        "game_type": "NLH",
        "game_subtype": "REGULAR"
    }
    response = api_client.post(f"/v1/clubs/{club.id}/tables", json=params)
    assert response.status_code == HTTP_201_CREATED
    table = TableProfile(**response.json())
    assert table
    assert table.id
    assert table.table_name == "TEST"
    assert table.table_type == "RG"
    assert table.table_seats == 6
    assert table.game_type == "NLH"
    assert table.game_subtype == "REGULAR"


    params = {
        "table_name": "TEST NLH AOF",
        "table_type": "RG",
        "table_seats": 6,
        "game_type": "NLH",
        "game_subtype": "AOF"
    }
    response = api_client.post(f"/v1/clubs/{club.id}/tables", json=params)
    assert response.status_code == HTTP_201_CREATED
    table = TableProfile(**response.json())
    assert table
    assert table.id
    assert table.table_name == "TEST NLH AOF"
    assert table.table_type == "RG"
    assert table.table_seats == 6
    assert table.game_type == "NLH"
    assert table.game_subtype == "AOF"


    # get tables
    response = api_client.get(f"/v1/clubs/{club.id}/tables")
    assert response.status_code == HTTP_200_OK
    tables = [TableProfile(**x) for x in response.json()]
    assert tables and len(tables)==2



def test_create_table_with_validation(api_client: TestClient, api_guest: UserAccessProfile):
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}

    params = {}
    response = api_client.post("/v1/clubs", json=params)
    club = ClubProfile(**response.json())

    params = {
        "table_name": "TEST",
        "table_type": "RG",
        "table_seats": 6,
        "game_type": "NLH",
        "game_subtype": "REGULAR",
        "props": {
            "buyin_min": 0,
            "buyin_max": 0,
            "buyin_cost": 0,
            "buyin_value": 0,
            "late_entry_level": 0,
            "rebuy_cost": 0,
            "rebuy_value": 0,
            "rebuy_count": 0,
            "addon_cost": 0,
            "addon_value": 0,
            "addon_level": 0,
            "blind_value": 0,
            "blind_schedule": "string",
            "blind_time": 1,
            "chat_mode": "ALL",
            "jackpot": False,
            "access_countries": ["1", "2", "3"]
        }
    }

    successfully_created_table_response = api_client.post(f"/v1/clubs/{club.id}/tables", json=params)
    assert successfully_created_table_response.status_code == 201

    params = {
        "table_name": "TEST",
        "table_type": "test",
        "table_seats": 6,
        "game_type": "NLH",
        "game_subtype": "REGULAR"
        }
    error_validate_in_table_type_response = api_client.post(f"/v1/clubs/{club.id}/tables", json=params)
    assert error_validate_in_table_type_response.status_code == 422

    params = {
        "table_name": "TEST",
        "table_type": "RG",
        "table_seats": 6,
        "game_type": "test",
        "game_subtype": "REGULAR"
    }
    error_validate_in_game_type_response = api_client.post(f"/v1/clubs/{club.id}/tables", json=params)
    assert error_validate_in_game_type_response.status_code == 422

    params = {
        "table_name": "TEST",
        "table_type": "RG",
        "table_seats": 6,
        "game_type": "NLH",
        "game_subtype": "test"
    }
    error_validate_in_game_subtype_response = api_client.post(f"/v1/clubs/{club.id}/tables", json=params)
    assert error_validate_in_game_subtype_response.status_code == 422

    params = {
        "table_name": "TEST",
        "table_type": "RG",
        "table_seats": 6,
        "game_type": "NLH",
        "game_subtype": "AOF",
        "deny_countries": [1, 2, 3]

    }
    error_validate_in_access_countries_response = api_client.post(f"/v1/clubs/{club.id}/tables", json=params)
    assert error_validate_in_access_countries_response.status_code == 422

    params = {
        "table_name": "TEST",
        "table_type": "RG",
        "table_seats": 6,
        "game_type": "NLH",
        "game_subtype": "AOF",
        "jackpot": 'test'
    }
    error_validate_in_boolean_attributes_response = api_client.post(f"/v1/clubs/{club.id}/tables", json=params)
    assert error_validate_in_boolean_attributes_response.status_code == 422

    params = {
        "table_name": "TEST",
        "table_type": "MTT",
        "table_seats": 6,
        "game_type": "NLH",
        "game_subtype": "AOF",
        "blind_level_time": 50
    }
    error_validate_in_blind_level_time_attributes_response = api_client.post(f"/v1/clubs/{club.id}/tables", json=params)
    assert error_validate_in_blind_level_time_attributes_response.status_code == 422

    params = {
        "table_name": "TEST",
        "table_type": "RG",
        "table_seats": 6,
        "game_type": "NLH",
        "game_subtype": "AOF",
        "access_password": "000"

    }
    error_validate_in_access_password_attributes_response = api_client.post(f"/v1/clubs/{club.id}/tables", json=params)
    assert error_validate_in_access_password_attributes_response.status_code == 422

    params['unknown_field'] = "unknown_value"
    error_validate_in_access_password_attributes_response = api_client.post(f"/v1/clubs/{club.id}/tables", json=params)
    assert error_validate_in_access_password_attributes_response.status_code == 422