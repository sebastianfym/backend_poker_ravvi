import pytest
pytestmark = pytest. mark. skip()

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


def test_tables_creation():
    # Регистрируем пользователя
    access_token, _ = register_guest()

    # Создаем клуб
    json = {"name": "club 1"}
    headers = {"Authorization": "Bearer " + access_token}
    response = client.post("/v1/clubs", json=json, headers=headers)
    assert response.status_code == 201

    club = response.json()

    # Создаем стол NLH
    json = {
        "table_type": "RING_GAME",
        "table_seats": 6,
        "game_type": "NLH",
        "game_subtype": "REGULAR"
    }
    response = client.post(f"/v1/clubs/{club['id']}/tables", json=json, headers=headers)
    assert response.status_code == 201

    nlh_table = response.json()
    assert nlh_table["table_type"] == json["table_type"]
    assert nlh_table["table_seats"] == json["table_seats"]
    assert nlh_table["game_type"] == json["game_type"]
    assert nlh_table["game_subtype"] == json["game_subtype"]

    # Создаем стол NLH AOF
    json = {
        "table_type": "RING_GAME",
        "table_seats": 6,
        "game_type": "NLH",
        "game_subtype": "AOF"
    }
    response = client.post(f"/v1/clubs/{club['id']}/tables", json=json, headers=headers)
    assert response.status_code == 201

    nlh_aof_table = response.json()
    assert nlh_aof_table["table_type"] == json["table_type"]
    assert nlh_aof_table["table_seats"] == json["table_seats"]
    assert nlh_aof_table["game_type"] == json["game_type"]
    assert nlh_aof_table["game_subtype"] == json["game_subtype"]

    # Создаем стол NLH 6+
    json = {
        "table_type": "RING_GAME",
        "table_seats": 6,
        "game_type": "NLH",
        "game_subtype": "6+"
    }
    response = client.post(f"/v1/clubs/{club['id']}/tables", json=json, headers=headers)
    assert response.status_code == 201

    nlh_6_table = response.json()
    assert nlh_6_table["table_type"] == json["table_type"]
    assert nlh_6_table["table_seats"] == json["table_seats"]
    assert nlh_6_table["game_type"] == json["game_type"]
    assert nlh_6_table["game_subtype"] == json["game_subtype"]

    # Создаем стол PLO
    json = {
        "table_type": "RING_GAME",
        "table_seats": 6,
        "game_type": "PLO",
        "game_subtype": "PLO6"
    }
    response = client.post(f"/v1/clubs/{club['id']}/tables", json=json, headers=headers)
    assert response.status_code == 201

    plo_table = response.json()
    assert plo_table["table_type"] == json["table_type"]
    assert plo_table["table_seats"] == json["table_seats"]
    assert plo_table["game_type"] == json["game_type"]
    assert plo_table["game_subtype"] == json["game_subtype"]

    # Создаем стол OFC
    json = {
        "table_type": "RING_GAME",
        "table_seats": 2,
        "game_type": "OFC",
        "game_subtype": "test"
    }
    response = client.post(f"/v1/clubs/{club['id']}/tables", json=json, headers=headers)
    assert response.status_code == 201

    ofc_table = response.json()
    assert ofc_table["table_type"] == json["table_type"]
    assert ofc_table["table_seats"] == json["table_seats"]
    assert ofc_table["game_type"] == json["game_type"]
    assert ofc_table["game_subtype"] == json["game_subtype"]


def test_create_club_table():
    # Создаем пользователя
    access_token, _ = register_guest()

    # Создаем другого пользователя
    new_access_token, _ = register_guest()

    # Создаем клуб 1ого пользователя
    json = {"name": "club 1"}
    headers = {"Authorization": "Bearer " + access_token}
    response = client.post("/v1/clubs", json=json, headers=headers)
    assert response.status_code == 201

    club = response.json()

    # Создаем клуб 2ого пользователя
    new_json = {"name": "club 2"}
    new_headers = {"Authorization": "Bearer " + new_access_token}
    new_response = client.post("/v1/clubs", json=new_json, headers=new_headers)
    assert new_response.status_code == 201

    new_club = new_response.json()

    # Пытаемся создать стол несуществующего клуба
    non_club_id = new_club["id"] + 100500
    json = {
        "table_type": "RING_GAME",
        "table_seats": 6,
        "game_type": "PLO",
        "game_subtype": "PLO6"
    }
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
    assert table["table_seats"] == json["table_seats"]
    assert table["game_type"] == json["game_type"]

    # Проверяем, что стол отобразился в списке доступных столов клуба
    response = client.get(f"/v1/clubs/{club['id']}/tables", headers=headers)
    assert response.status_code == 200

    club_tables = response.json()

    club_table = list(filter(lambda x: x["id"] == table["id"], club_tables))
    assert len(club_table) == 1
    assert club_table[0]["id"] == table["id"]


def test_get_club_tables():
    # Регистрируем пользователя
    access_token, _ = register_guest()

    # Создаем клуб
    json = {"name": "club 1"}
    headers = {"Authorization": "Bearer " + access_token}
    response = client.post("/v1/clubs", json=json, headers=headers)
    assert response.status_code == 201

    club = response.json()

    # Создаем стол
    json = {
        "table_type": "RING_GAME",
        "table_seats": 6,
        "game_type": "PLO",
        "game_subtype": "PLO6"
    }
    response = client.post(f"/v1/clubs/{club['id']}/tables", json=json, headers=headers)
    assert response.status_code == 201

    table = response.json()

    # Получаем столы существующего клуба
    response = client.get(f"/v1/clubs/{club['id']}/tables", headers=headers)
    assert response.status_code == 200

    tables = response.json()

    assert len(tables) == 1
    assert tables[0]["id"]
    assert tables[0]["club_id"] == club["id"]
    assert tables[0]["table_name"] == table["table_name"]
    assert tables[0]["table_type"] == table["table_type"]
    assert tables[0]["game_type"]== table["game_type"]
    assert tables[0]["game_subtype"]== table["game_subtype"]

    # Пытаемся получить столы несуществующего клуба
    non_club_id = club["id"] + 100500
    response = client.get(f"/v1/clubs/{non_club_id}/tables", headers=headers)
    assert response.status_code == 404

    # Регистрируем нового пользователя (не участника)
    new_access_token, _ = register_guest()

    # Пытаемся получить столы существующего клуба не участником
    new_headers = {"Authorization": "Bearer " + new_access_token}
    response = client.get(f"/v1/clubs/{club['id']}/tables", headers=new_headers)
    assert response.status_code == 403
