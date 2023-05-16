from fastapi.testclient import TestClient

from ravvi_poker_backend.api.main import app

client = TestClient(app)


def register_guest():
    response = client.post("/v1/auth/register", json={})
    assert response.status_code == 200
    result = response.json()
    username = result["username"]
    access_token = result["access_token"]
    return access_token, username


def test_21_tables():
    # register new guest
    access_token, username = register_guest()
    headers = {"Authorization": "Bearer " + access_token}

    # create club
    params = dict(name="test_21")
    response = client.post("/v1/clubs", headers=headers, json=params)
    assert response.status_code == 200
    club = response.json()
    assert club["id"]
    assert club["name"] == "test_21"
    club_id = club["id"]

    # create table
    params = dict()
    response = client.post(f"/v1/clubs/{club_id}/tables", headers=headers, json=params)
    assert response.status_code == 200
    table_1 = response.json()
    assert table_1["id"]
    assert table_1["club_id"] == club_id

    # create table
    response = client.post(f"/v1/clubs/{club_id}/tables", headers=headers, json=params)
    assert response.status_code == 200
    table_2 = response.json()
    assert table_2["id"]
    assert table_2["club_id"] == club_id

    # list clubs
    response = client.get(f"/v1/clubs/{club_id}/tables", headers=headers)
    assert response.status_code == 200
    tables = response.json()
    assert isinstance(tables, list)
    assert len(tables)==2
    tables.sort(key=lambda x: x['id'])
    tables_A = tables[0]
    assert tables_A['id'] == table_1["id"]
    assert tables_A['club_id'] == club_id
    tables_B = tables[1]
    assert tables_B['id'] == table_2["id"]
    assert tables_B['club_id'] == club_id

    # get table
    table_id = tables_A['id']
    response = client.get(f"/v1/tables/{table_id}", headers=headers)
    assert response.status_code == 200
    table_A_profile = response.json()
    assert table_A_profile["id"] == table_id
    assert table_A_profile["club_id"] == club_id

    # update table
    # TODO
    #params = dict(name="test_20_C")
    #response = client.put(f"/v1/tables/{table_id}", headers=headers, json=params)
    #assert response.status_code == 200

