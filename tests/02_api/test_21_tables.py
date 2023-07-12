from fastapi.testclient import TestClient

from ravvi_poker.api.main import app

client = TestClient(app)


def register_guest():
    response = client.post("/v1/auth/register", json={})
    assert response.status_code == 200
    result = response.json()
    username = result["username"]
    access_token = result["access_token"]
    return access_token, username


def test_create_club_table():
    # Создаем пользователя
    access_token, _ = register_guest()

    # Создаем другого пользователя
    new_access_token, _ = register_guest()

    # Создаем клуб 1ого пользователя
    json = {"name": "club 1"}
    headers = {"Authorization": "Bearer " + access_token}
    response = client.post("/v1/clubs", json=json, headers=headers)
    assert response.status_code == 200

    club = response.json()

    # Создаем клуб 2ого пользователя
    new_json = {"name": "club 2"}
    new_headers = {"Authorization": "Bearer " + new_access_token}
    new_response = client.post("/v1/clubs", json=new_json, headers=new_headers)
    assert new_response.status_code == 200

    new_club = new_response.json()

    # Пытаемся создать стол несуществующего клуба
    non_club_id = new_club["id"] + 100500
    json = {"table_name": "table", "table_type": "type", "game_type": "game type"}
    response = client.post(f"/v1/clubs/{non_club_id}/tables", json=json, headers=headers)
    assert response.status_code == 404

    # Пытаемся создать стол в чужом клубе
    response = client.post(f"/v1/clubs/{new_club['id']}/tables", json=json, headers=headers)
    assert response.status_code == 403

    # Создаем стол в своем клубе
    response = client.post(f"/v1/clubs/{club['id']}/tables", json=json, headers=headers)
    assert response.status_code == 201

    table = response.json()
    assert table["id"]
    assert table["table_name"] == json["table_name"]
    assert table["table_type"] == json["table_type"]
    assert table["game_type"] == json["game_type"]

    # Проверяем, что стол отобразился в списке доступных столов клуба
    response = client.get(f"/v1/clubs/{club['id']}/tables", headers=headers)
    assert response.status_code == 200

    club_tables = response.json()

    club_table = list(filter(lambda x: x["id"] == table["id"], club_tables["tables"]))
    assert len(club_table) == 1
    assert club_table[0]["id"] == table["id"]

    # Удаляем стол
    response = client.delete(f"/v1/clubs/{club['id']}/tables/{table['id']}", headers=headers)
    assert response.status_code == 204


def test_delete_club_table():
    # Создаем пользователя
    access_token, _ = register_guest()

    # Создаем другого пользователя
    new_access_token, _ = register_guest()

    # Создаем клуб 1ого пользователя
    json = {"name": "club 1"}
    headers = {"Authorization": "Bearer " + access_token}
    response = client.post("/v1/clubs", json=json, headers=headers)
    assert response.status_code == 200

    club = response.json()

    # Создаем стол
    json = {"table_name": "table", "table_type": "type", "game_type": "game type"}
    response = client.post(f"/v1/clubs/{club['id']}/tables", json=json, headers=headers)
    assert response.status_code == 201

    table = response.json()

    # Пытаемся удалить стол несуществующего клуба
    non_club_id = club["id"] + 100500
    response = client.delete(f"/v1/clubs/{non_club_id}/tables/{table['id']}", headers=headers)
    assert response.status_code == 404

    # Пытаемся удалить несуществующий стол существующего клуба
    non_table_id = table["id"] + 100500
    response = client.delete(f"/v1/clubs/{club['id']}/tables/{non_table_id}", headers=headers)
    assert response.status_code == 404

    # Пытаемся удалить сущ стол в сущ клубе не владельцем
    new_headers = {"Authorization": "Bearer " + new_access_token}
    response = client.delete(f"/v1/clubs/{club['id']}/tables/{table['id']}", headers=new_headers)
    assert response.status_code == 403

    # Проверка доступности стола
    response = client.get(f"/v1/clubs/{club['id']}/tables", headers=headers)
    assert response.status_code == 200

    club_tables = response.json()

    club_table = list(filter(lambda x: x["id"] == table["id"], club_tables["tables"]))
    assert len(club_table) == 1
    assert club_table[0]["id"] == table["id"]

    # Удаляем владельцем клуба
    response = client.delete(f"/v1/clubs/{club['id']}/tables/{table['id']}", headers=headers)
    assert response.status_code == 204

    # Проверка доступности стола
    response = client.get(f"/v1/clubs/{club['id']}/tables", headers=headers)
    assert response.status_code == 200

    club_tables = response.json()

    club_table = list(filter(lambda x: x["id"] == table["id"], club_tables["tables"]))
    assert not club_table

    # Попытка удаления удаленного стола
    response = client.delete(f"/v1/clubs/{club['id']}/tables/{table['id']}", headers=headers)
    assert response.status_code == 404


def test_get_club_tables():
    # TODO закончить
    pass


# def test_21_tables():
#     # register new guest
#     access_token, username = register_guest()
#     headers = {"Authorization": "Bearer " + access_token}

#     # create club
#     params = dict(name="test_21")
#     response = client.post("/v1/clubs", headers=headers, json=params)
#     assert response.status_code == 200
#     club = response.json()
#     assert club["id"]
#     assert club["name"] == "test_21"
#     club_id = club["id"]

#     # create table
#     params = dict()
#     response = client.post(f"/v1/clubs/{club_id}/tables", headers=headers, json=params)
#     assert response.status_code == 200
#     table_1 = response.json()
#     assert table_1["id"]
#     assert table_1["club_id"] == club_id

#     # create table
#     response = client.post(f"/v1/clubs/{club_id}/tables", headers=headers, json=params)
#     assert response.status_code == 200
#     table_2 = response.json()
#     assert table_2["id"]
#     assert table_2["club_id"] == club_id

#     # list clubs
#     response = client.get(f"/v1/clubs/{club_id}/tables", headers=headers)
#     assert response.status_code == 200
#     tables = response.json()
#     assert isinstance(tables, list)
#     assert len(tables)==2
#     tables.sort(key=lambda x: x['id'])
#     tables_A = tables[0]
#     assert tables_A['id'] == table_1["id"]
#     assert tables_A['club_id'] == club_id
#     tables_B = tables[1]
#     assert tables_B['id'] == table_2["id"]
#     assert tables_B['club_id'] == club_id

#     # get table
#     table_id = tables_A['id']
#     response = client.get(f"/v1/tables/{table_id}", headers=headers)
#     assert response.status_code == 200
#     table_A_profile = response.json()
#     assert table_A_profile["id"] == table_id
#     assert table_A_profile["club_id"] == club_id

#     # TODO update table
#     # params = dict(name="test_20_C")
#     # response = client.put(f"/v1/tables/{table_id}", headers=headers, json=params)
#     # assert response.status_code == 200
