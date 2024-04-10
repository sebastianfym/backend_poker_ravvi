import pytest
import pytest_asyncio

from helpers.api_client import APITestClient
from ravvi_poker.api.chips.club import ChipsTxnInfo

def test_chips_txn_club_smoke():
    owner = APITestClient()
    owner.register()
    owner.create_club()

    params = {'action': 'IN', 'amount': 100}
    response = owner.post(f'/api/v1/clubs/{owner.club.id}/chips', json=params)
    assert response.status_code == 201
    owner.use_club()
    assert owner.club.club_balance == 100
    

    params = {'action': 'OUT', 'amount': 25}
    response = owner.post(f'/api/v1/clubs/{owner.club.id}/chips', json=params)
    assert response.status_code == 201
    owner.use_club()
    assert owner.club.club_balance == 75


    data = owner.get_txns_club()
    txns, users = data.txns, data.users
    users = {u.id:u for u in users}
    assert len(txns) == 2
    x = txns[0]
    assert x.txn_id
    assert x.txn_type == 'CHIPSIN'
    assert x.txn_delta == 100
    assert x.created_ts
    assert x.created_by in users
    assert x.created_by == owner.user_id
    assert x.user_id is None

    x = txns[1]
    assert x.txn_id
    assert x.txn_type == 'CHIPSOUT'
    assert x.txn_delta == -25
    assert x.created_ts
    assert x.created_by in users
    assert x.created_by == owner.user_id
    assert x.user_id is None



def test_chips_txn_club_negative_validation():
    owner = APITestClient()
    owner.register()
    owner.create_club()

    params = {}
    response = owner.post(f'/api/v1/clubs/{owner.club.id}/chips', json=params)
    assert response.status_code == 422

    params = {'action': 'XXX', 'amount': 1}
    response = owner.post(f'/api/v1/clubs/{owner.club.id}/chips', json=params)
    assert response.status_code == 400

    params = {'action': 'IN', 'amount': 0}
    response = owner.post(f'/api/v1/clubs/{owner.club.id}/chips', json=params)
    print(response.json())
    assert response.status_code == 422

    params = {'action': 'IN', 'amount': -1}
    response = owner.post(f'/api/v1/clubs/{owner.club.id}/chips', json=params)
    print(response.json())
    assert response.status_code == 422

    params = {'action': 'OUT', 'amount': 1, 'uknown_attribute': 666}
    response = owner.post(f'/api/v1/clubs/{owner.club.id}/chips', json=params)
    print(response.json())
    assert response.status_code == 422

