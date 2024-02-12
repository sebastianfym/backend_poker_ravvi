import json
from decimal import Decimal

import pytest

from fastapi.testclient import TestClient
from ravvi_poker.api.auth import UserAccessProfile
from ravvi_poker.api.clubs import ClubProfile, ClubMemberProfile
from ravvi_poker.db import DBI


def test_create_club(api_client: TestClient, api_guest: UserAccessProfile, api_client_2: TestClient,
                     api_guest_2: UserAccessProfile):
    club_404 = 4040404040
    # set headers
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}
    api_client_2.headers = {"Authorization": "Bearer " + api_guest_2.access_token}

    # create club without props (defaults)
    params = {}
    response = api_client.post("/v1/clubs", json=params)
    assert response.status_code == 201

    club1 = ClubProfile(**response.json())
    assert club1.id
    assert club1.name.startswith("CLUB-")
    assert club1.description is None
    assert club1.image_id is None
    assert club1.user_role == "O"
    assert club1.user_approved is True

    # create club with props
    params = {"name": "New club", "description": "Desc"}
    response = api_client.post("/v1/clubs", json=params)
    assert response.status_code == 201

    club2 = ClubProfile(**response.json())
    assert club2.id
    assert club2.name == "New club"
    assert club2.description == "Desc"
    assert club2.image_id is None
    assert club2.user_role == "O"
    assert club2.user_approved is True

    # get my clubs
    response = api_client.get("/v1/clubs")
    assert response.status_code == 200

    # check my clubs
    my_clubs = list(map(lambda x: ClubProfile(**x), response.json()))
    assert len(my_clubs) == 2
    # assert club1["id"] in my_clubs_ids
    # assert club2["id"] in my_clubs_ids

    # update club2
    params = {"name": "Some new name", "description": "Some new desc"}
    response = api_client.patch(f"/v1/clubs/{club2.id}", json=params)
    assert response.status_code == 200

    club2 = ClubProfile(**response.json())
    assert club2.id
    assert club2.name == "Some new name"
    assert club2.description == "Some new desc"
    assert club2.image_id is None
    assert club2.user_role == "O"
    assert club2.user_approved is True

    # get club2 by new user
    response = api_client_2.post(f"/v1/clubs/{club2.id}/members")
    assert response.status_code == 200
    response = api_client_2.get(f"/v1/clubs/{club2.id}")
    assert response.status_code == 200
    club2_2 = ClubProfile(**response.json())
    assert club2_2.id == club2.id
    assert club2_2.user_role == "P"
    assert club2_2.user_approved is False

    response = api_client_2.get(f"/v1/clubs/{club_404}")
    assert response.status_code == 404

    # update club2 by new user
    params = {"name": "User 2 new name"}
    response = api_client_2.patch(f"/v1/clubs/{club2.id}", json=params)
    assert response.status_code == 403

    response = api_client_2.patch(f"/v1/clubs/{club_404}", json=params)
    assert response.status_code == 404

    # delete club2 by new user
    # response = client.delete(f"/v1/clubs/{club2['id']}", headers=new_headers)
    # assert response.status_code == 403

    # delete club2 by user
    # response = client.delete(f"/v1/clubs/{club2['id']}", headers=headers)
    # assert response.status_code == 204

    # create and get clubs tables

    params = {
        "table_name": "TEST",
        "table_type": "RG",
        "table_seats": 6,
        "game_type": "NLH",
        "game_subtype": "REGULAR"
    }
    response = api_client.post(f"/v1/clubs/{club1.id}/tables", json=params)
    assert response.status_code == 201

    response = api_client.get(f"/v1/clubs/{club1.id}/tables")
    assert response.status_code == 200
    assert isinstance(response.json(), list) is True
    assert response.json() != []


def test_21_club_join(api_client: TestClient, api_guest: UserAccessProfile, api_client_2: TestClient,
                      api_guest_2: UserAccessProfile):
    # set headers
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}
    api_client_2.headers = {"Authorization": "Bearer " + api_guest_2.access_token}

    # create club without props (defaults)
    response = api_client.post("/v1/clubs", json={})
    assert response.status_code == 201
    club = ClubProfile(**response.json())

    response = api_client_2.post(f"/v1/clubs/{club.id}/members")
    assert response.status_code == 200
    club_2 = ClubProfile(**response.json())
    assert club_2.id
    assert club_2.name
    assert club_2.user_role == 'P'
    assert club_2.user_approved is False

    # list clubs
    response = api_client.get("/v1/clubs")
    assert response.status_code == 200
    clubs = response.json()
    assert clubs

    # response = api_client_2.get("/v1/clubs")
    # assert response.status_code == 200
    # clubs = response.json()
    # assert clubs

    # list members
    response = api_client.get(f"/v1/clubs/{club.id}/members")
    assert response.status_code == 200
    members = [ClubMemberProfile(**m) for m in response.json()]
    pending = [m for m in members if not m.user_approved]
    assert members
    assert pending and len(pending) == 1

    # approve
    p = pending[0]
    response = api_client.put(f"/v1/clubs/{club.id}/members/{p.id}")
    assert response.status_code == 200
    member = ClubMemberProfile(**response.json())
    assert member.user_approved

    response = api_client.post(
        f"/v1/clubs/{23131232141241212512512125125551525252152151251252151554554765634353534534}/members")
    assert response.status_code == 404
    assert response.json() == {"detail": "Club not found"}

    response = api_client.post(
        f"/v1/clubs/{23131232141241212512512125125551525252152151251252151554554765634353534534}/members")
    assert response.status_code == 404
    assert response.json() == {"detail": "Club not found"}

    response = api_client.put(
        f"/v1/clubs/{23131232141241212512512125125551525252152151251252151554554765634353534534}/members/{p.id}")
    assert response.status_code == 404
    assert response.json() == {"detail": "Club not found"}

    response = api_client.put(f"/v1/clubs/{club.id}/members/{1231242521215253634645748567856345235252362346354747544}")
    assert response.status_code == 404
    assert response.json() == {'detail': 'Member not found'}


def test_get_relations(api_client: TestClient, api_guest: UserAccessProfile):
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}

    params = {}
    response = api_client.post("/v1/clubs", json=params)
    assert response.status_code == 201

    club = ClubProfile(**response.json())
    response = api_client.get(f'/v1/clubs/{club.id}/relation_clubs')
    assert response.status_code == 200
    assert isinstance(response.json(), list)

    response = api_client.get(f"/v1/clubs/{club.id}/relation_union")
    assert response.status_code == 404
    assert response.json() == {'detail': 'Union not found'}


def test_get_club(api_client: TestClient, api_guest: UserAccessProfile):
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}

    # create club without props (defaults)
    params = {}
    response = api_client.post("/v1/clubs", json=params)
    assert response.status_code == 201

    club = ClubProfile(**response.json())
    assert club.id
    assert club.user_role == "O"

    response = api_client.get("/v1/clubs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert response.json()[0]['user_balance'] == 0.0
    assert response.json()[0]['agents_balance'] == 0.0
    assert response.json()[0]['club_balance'] == 0.0
    assert response.json()[0]['service_balance'] == 0.0

    club.user_role = 'P'
    assert club.club_balance == 0.0
    assert club.service_balance == 0.0
    assert club.agents_balance == 0.0


def test_txn_balance_club(api_client: TestClient, api_guest: UserAccessProfile, api_client_2: TestClient,
                          api_guest_2: UserAccessProfile):
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}
    api_client_2.headers = {"Authorization": "Bearer " + api_guest_2.access_token}

    params = {}
    response = api_client.post("/v1/clubs", json=params)
    assert response.status_code == 201

    club = ClubProfile(**response.json())

    # Actions with manipulations of the club's balance

    # response = api_client.post(f"/v1/clubs/{club.id}/add_chip_on_club_balance", json={})
    # assert response.status_code == 200
    # assert response.json()['status_code'] == 400
    # assert response.json()['detail'] == 'You forgot to amount out quantity the chips'

    # TODO перенес в test_add_chips_to_club
    # response = api_client.post(f"/v1/clubs/{club.id}/add_chip_on_club_balance", json={"amount": 1000.00})
    # assert response.status_code == 200
    # response = api_client.get(f"/v1/clubs/{club.id}")
    # assert response.json()['club_balance'] == 1000
    # assert response.status_code == 200

    # TODO перенес в test_add_chips_to_club
    # response = api_client.post(f"/v1/clubs/{club.id}/add_chip_on_club_balance", json={})
    # assert response.status_code == 200
    # assert response.json()['status_code'] == 400
    # assert response.json()['detail'] == 'You forgot to amount out quantity the chips'

    # TODO перенес в test_delete_chips_to_club
    # response = api_client.post(f"/v1/clubs/{club.id}/delete_chip_from_club_balance", json={})
    # assert response.status_code == 200
    # assert response.json()['status_code'] == 400
    # assert response.json()['detail'] == "You forgot to add a value: 'amount'"

    # TODO перенес в test_delete_chips_to_club
    # response = api_client.post(f"/v1/clubs/{club.id}/delete_chip_from_club_balance", json={"amount": 1})
    # assert response.status_code == 200
    # response = api_client.get(f"/v1/clubs/{club.id}")
    # assert response.status_code == 200
    # assert response.json()['club_balance'] == 999

    # TODO перенес в test_delete_chips_to_club
    # response = api_client_2.post(f"/v1/clubs/{club.id}/delete_chip_from_club_balance", json={"amount": 1})
    # assert response.json()['status_code'] == 403
    #
    # #Action with manipulations of the club's user balance
    #
    #
    # response = api_client.post(f"/v1/clubs/{club.id}/giving_chips_to_the_user", json={"amount": 1})
    # assert response.json()['status_code'] == 400
    # assert response.json()['detail'] == "You forgot to add a value: 'balance'"
    #
    # response = api_client.post(f"/v1/clubs/{club.id}/giving_chips_to_the_user", json={"user_id": 1})
    # assert response.json()['status_code'] == 400
    # assert response.json()['detail'] == "You forgot to add a value: 'amount'"
    #
    # response = api_client.post(f"/v1/clubs/{club.id}/giving_chips_to_the_user", json={"amount": 1, "user_id": 1})
    # assert response.json()['status_code'] == 400
    # assert response.json()['detail'] == "You forgot to add a value: 'balance'"
    #
    # response = api_client_2.post(f"/v1/clubs/{club.id}/giving_chips_to_the_user", json={"amount": 1, "user_id": 1, "balance": "user_balance"})
    # assert response.json()['status_code'] == 403
    # assert response.json()['detail'] == "You don't have enough rights to perform this action"
    #
    # response = api_client.post(f"/v1/clubs/{club.id}/delete_chips_from_the_user", json={"amount": 1, "user_id": 1, "balance": "user_balance"})
    # assert response.json() == 200
    #
    # response = api_client.post(f"/v1/clubs/{club.id}/delete_chips_from_the_user", json={"amount": 1})
    # assert response.json()['status_code'] == 400
    # assert response.json()['detail'] == "You forgot to add a value: 'user_id'"
    #
    # response = api_client.post(f"/v1/clubs/{club.id}/delete_chips_from_the_user", json={"user_id": 1})
    # assert response.json()['status_code'] == 400
    # assert response.json()['detail'] == "You forgot to add a value: 'amount'"
    #
    # response = api_client.post(f"/v1/clubs/{club.id}/delete_chips_from_the_user", json={"amount": 1, "user_id": 1})
    # assert response.json()['status_code'] == 400
    # assert response.json()['detail'] == "You forgot to add a value: 'balance'"
    #
    # response = api_client_2.post(f"/v1/clubs/{club.id}/delete_chips_from_the_user", json={"amount": 1, "user_id": 1, "balance": "user_balance"})
    # assert response.json()['status_code'] == 403
    # assert response.json()['detail'] == "You don't have enough rights to perform this action"
    #
    # #The user requests chips from the club
    #
    # response = api_client.post(f"/v1/clubs/{club.id}/request_chips", json={"amount": 1, "balance": "balance_shared"})
    # assert response.status_code == 200
    #
    # response = api_client.post(f"/v1/clubs/{club.id}/request_chips", json={"amount": 1})
    # assert response.json()['status_code'] == 400
    # assert response.json()['detail'] == "You forgot to add a value: 'balance'"
    #
    # response = api_client.post(f"/v1/clubs/{club.id}/request_chips", json={"balance": "balance_shared"})
    # assert response.json()['status_code'] == 400
    # assert response.json()['detail'] == "You forgot to add a value: 'amount'"
    #
    # response = api_client_2.post(f"/v1/clubs/{club.id}/request_chips", json={"amount": 1, "balance": "balance_shared"})
    # assert response.json()['status_code'] == 403
    # assert response.json()['detail'] == "You don't have enough rights to perform this action"
    #
    # #TXN info
    #
    # response = api_client.get(f"/v1/info/{club.id}/history")
    # assert response.status_code == 200
    # assert response.json()[0]['txn_type'] == 'CLUB_CASHIN'
    # assert response.json()[1]['txn_type'] == 'CLUB_REMOVE'
    # assert response.json()[2]['txn_type'] == 'replenishment'
    # assert isinstance(response.json(), list)


@pytest.fixture
def client(request, api_client: TestClient, api_guest: UserAccessProfile,
           api_client_2: TestClient, api_guest_2: UserAccessProfile):
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}
    if request.__dict__["param"] == "get_authorize_client":
        api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}
        yield api_client
    elif request.__dict__["param"] == "get_two_clients":
        api_client_2.headers = {"Authorization": "Bearer " + api_guest_2.access_token}
        yield [api_client, api_client_2]


def create_club(client: list[TestClient] | TestClient):
    params = {}
    if isinstance(client, list):
        response = client[0].post("/v1/clubs", json=params)
    elif isinstance(client, TestClient):
        response = client.post("/v1/clubs", json=params)
    else:
        raise ValueError("incorrect client type")
    club = ClubProfile(**response.json())

    return club


@pytest.mark.parametrize("client, request_params, status_code, club_balance",
                         [
                             ["get_authorize_client", {"amount": -1000}, 422, None],
                             ["get_two_clients", {"amount": -1000}, 403, None],

                             ["get_authorize_client", {"amount": "very_bug_value"}, 422, None],
                             ["get_two_clients", {"amount": "very_bug_value"}, 403, None],

                             ["get_authorize_client", {"amound": 1000}, 422, None],
                             ["get_two_clients", {"amound": 1000}, 403, None],

                             ["get_authorize_client", {"amount": 10.555555555555555}, 422, None],
                             ["get_two_clients", {"amount": 10.555555555555555}, 403, None],

                             ["get_authorize_client", {"amount": "1000"}, 422, None],
                             ["get_two_clients", {"amount": "1000"}, 403, None],

                             ["get_authorize_client", {}, 422, None],
                             ["get_two_clients", {}, 403, None],

                             ["get_authorize_client", {"amount": 5.1547}, 422, None],
                             ["get_two_clients", {"amount": 5.1547}, 403, None],

                             ["get_authorize_client", {"amount": 10 ** 10}, 422, None],
                             ["get_two_clients", {"amount": 10 ** 10}, 403, None],

                             ["get_authorize_client", {"amount": 5.00}, 200, 5],
                             ["get_two_clients", {"amount": 5.00}, 403, None],

                             ["get_authorize_client", {"amount": 5.13}, 200, 5.13],
                             ["get_two_clients", {"amount": 5.13}, 403, None],

                             ["get_authorize_client", {"amount": 1000.00}, 200, 1000.00],
                             ["get_two_clients", {"amount": 1000.00}, 403, None],
                         ],
                         indirect=["client"])
def test_add_chips_to_club(client, request_params, status_code, club_balance):
    club = create_club(client)
    if isinstance(client, list):
        # если у нас два клиента, значит второй неавторизованный
        client = client[1]

    response = client.post(f"/v1/clubs/{club.id}/add_chip_on_club_balance", json=request_params)
    assert response.status_code == status_code

    if club_balance is not None:
        response = client.get(f"/v1/clubs/{club.id}")
        assert response.json()['club_balance'] == club_balance


def test_add_chips_rounding(api_client: TestClient, api_guest: UserAccessProfile, api_client_2: TestClient,
                            api_guest_2: UserAccessProfile):
    """
    Проверяем округление
    """
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}
    api_client_2.headers = {"Authorization": "Bearer " + api_guest_2.access_token}

    params = {}
    response = api_client.post("/v1/clubs", json=params)
    club = ClubProfile(**response.json())

    response = api_client.post(f"/v1/clubs/{club.id}/add_chip_on_club_balance", json={"amount": 1000})
    assert response.status_code == 200
    response = api_client.get(f"/v1/clubs/{club.id}")
    assert response.json()['club_balance'] == 1000

    response = api_client.post(f"/v1/clubs/{club.id}/add_chip_on_club_balance", json={"amount": 0.12})
    assert response.status_code == 200
    response = api_client.get(f"/v1/clubs/{club.id}")
    assert response.json()['club_balance'] == 1000.12

    response = api_client.post(f"/v1/clubs/{club.id}/add_chip_on_club_balance", json={"amount": 0.07})
    assert response.status_code == 200
    response = api_client.get(f"/v1/clubs/{club.id}")
    assert response.json()['club_balance'] == 1000.19


@pytest.mark.parametrize("client, initial_club_balance, request_params, status_code, club_balance",
                         [
                             ["get_authorize_client", 100, {"amount": -1000}, 422, None],
                             ["get_two_clients", 100, {"amount": -1000}, 403, None],

                             ["get_authorize_client", 100, {"amount": "very_bug_value"}, 422, None],
                             ["get_two_clients", 100, {"amount": "very_bug_value"}, 403, None],

                             ["get_authorize_client", 100, {"amound": 1000}, 422, None],
                             ["get_two_clients", 100, {"amound": 1000}, 403, None],

                             ["get_authorize_client", 100, {"amount": 10.555555555555555}, 422, None],
                             ["get_two_clients", 100, {"amount": 10.555555555555555}, 403, None],

                             ["get_authorize_client", 100, {"amount": "1000"}, 422, None],
                             ["get_two_clients", 100, {"amount": "1000"}, 403, None],

                             ["get_authorize_client", 100, {}, 422, None],
                             ["get_two_clients", 100, {}, 403, None],

                             ["get_authorize_client", 100, {"amount": 5.1547}, 422, None],
                             ["get_two_clients", 100, {"amount": 5.1547}, 403, None],

                             ["get_authorize_client", 100, {"amount": 10 ** 10}, 422, None],
                             ["get_two_clients", 100, {"amount": 10 ** 10}, 403, None],

                             ["get_authorize_client", 100, {"amount": 5}, 200, 95],
                             ["get_two_clients", 100, {"amount": 5}, 403, None],

                             ["get_authorize_client", 100, {"amount": 5.13}, 200, 94.87],
                             ["get_two_clients", 100, {"amount": 5.13}, 403, None],

                             ["get_authorize_client", 100, {"amount": 1000.00}, 200, 0],
                             ["get_two_clients", 100, {"amount": 1000.00}, 403, None],
                         ],
                         indirect=["client"])
def test_delete_chips_to_club(client, initial_club_balance, request_params, status_code, club_balance):
    club = create_club(client)
    if isinstance(client, list):
        # если у нас два клиента, значит второй неавторизованный
        authorized_client, client = client[0], client[1]
    else:
        authorized_client = client

    # зачисляем первоначальные средства
    response = authorized_client.post(f"/v1/clubs/{club.id}/add_chip_on_club_balance", json={
        "amount": initial_club_balance})
    assert response.status_code == 200

    response = client.post(f"/v1/clubs/{club.id}/delete_chip_from_club_balance", json=request_params)
    assert response.status_code == status_code

    response = authorized_client.get(f"/v1/clubs/{club.id}")
    if club_balance is not None:
        assert response.json()['club_balance'] == club_balance
    else:
        assert response.json()['club_balance'] == initial_club_balance


def test_delete_chips_rounding(api_client: TestClient, api_guest: UserAccessProfile, api_client_2: TestClient,
                               api_guest_2: UserAccessProfile):
    """
    Проверяем округление
    """
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}
    api_client_2.headers = {"Authorization": "Bearer " + api_guest_2.access_token}

    params = {}
    response = api_client.post("/v1/clubs", json=params)
    club = ClubProfile(**response.json())

    response = api_client.post(f"/v1/clubs/{club.id}/add_chip_on_club_balance", json={"amount": 1000})
    assert response.status_code == 200
    response = api_client.get(f"/v1/clubs/{club.id}")
    assert response.json()['club_balance'] == 1000

    response = api_client.post(f"/v1/clubs/{club.id}/delete_chip_from_club_balance", json={"amount": 0.12})
    assert response.status_code == 200
    response = api_client.get(f"/v1/clubs/{club.id}")
    assert response.json()['club_balance'] == 999.88

    response = api_client.post(f"/v1/clubs/{club.id}/delete_chip_from_club_balance", json={"amount": 0.07})
    assert response.status_code == 200
    response = api_client.get(f"/v1/clubs/{club.id}")
    assert response.json()['club_balance'] == 999.81


@pytest.mark.asyncio
@pytest.mark.parametrize("amount, balance_type",
                         [
                             [10, "balance"],
                             [10.05, "balance"],

                             # [10, "balance_shared"],
                             # [10.05, "balance_shared"],
                         ])
async def test_giving_chips_to_the_user(api_client: TestClient, api_guest: UserAccessProfile, amount: int | float,
                                        balance_type: str):
    # получаем пользователя, который будет владельцем клуба
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}

    # создаем клуб от его лица
    club = create_club(api_client)

    # создаем пользователя, которому будет начислять фишки и заводим его в клуб
    async with DBI() as dbi:
        user_profile_to_get_chips = await dbi.create_user()
        user_account_to_get_chips = await dbi.create_club_member(club.id, user_profile_to_get_chips.id, "TEST_MEMBER")

    # начисляем фишки
    response = api_client.post(f"/v1/clubs/{club.id}/giving_chips_to_the_user",
                               json={"amount": amount, "recipient_user_id": user_account_to_get_chips.user_id,
                                     "balance": balance_type})
    assert response.status_code == 200

    async with DBI() as dbi:
        async with dbi.cursor() as cursor:
            # проверяем баланс
            await cursor.execute(f"SELECT {balance_type} FROM user_account WHERE id = %s AND club_id = %s",
                                 (user_account_to_get_chips.id, club.id))
            balance = await cursor.fetchone()
            # TODO окргуление
            assert getattr(balance, balance_type).quantize(Decimal('.01')) == Decimal(amount).quantize(Decimal('.01'))

            # проверяем транзакцию
            # cursor.execute("SELECT * FROM user_account_txn WHERE id = %s AND club_id = %s ")


def test_operations_at_the_checkout(api_client: TestClient, api_guest: UserAccessProfile):
    api_client.headers = {"Authorization": "Bearer " + api_guest.access_token}

    club = create_club(api_client)

    response = api_client.get(f"/v1/clubs/{club.id}/operations_at_the_checkout")

    assert response.status_code == 200
    assert response.json().get('club_balance') == 0.0
    assert response.json().get('members_balance') == 0.0
    assert response.json().get('agents_balance') == 0.0
    assert response.json().get('total_balance') == 0.0
    assert response.json().get('club_members')[0]['user_role'] == "O"
    assert response.json().get('club_members')[0]['balance'] == 0.0
    assert response.json().get('club_members')[0]['balance_shared'] == 0.0