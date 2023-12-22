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
