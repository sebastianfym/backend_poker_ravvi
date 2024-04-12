import pytest
import pytest_asyncio

from helpers.api_client import APITestClient

def test_chips_txn_player_smoke():
    owner = APITestClient()
    owner.register()
    owner.create_club()
    
    params = {'action': 'IN', 'amount': 1000}
    response = owner.post(f'/api/v1/clubs/{owner.club.id}/chips', json=params)
    assert response.status_code == 201
    owner.use_club()
    assert owner.club.club_balance == 1000 

    agent = APITestClient()
    agent.register()
    agent.use_club(owner.club.id)
    agent.join_club()

    owner.approve_member(agent.user_id, user_role='A')

    agent.use_club(owner.club.id)
    assert agent.club.user_role == 'A'

    params = {'action': 'IN', 'amount': 200}
    response = owner.post(f'/api/v1/clubs/{owner.club.id}/chips/players/{agent.user_id}', json=params)
    assert response.status_code == 201

    owner.use_club()
    assert owner.club.club_balance == 800 
    assert owner.club.user_balance == 0 
    assert owner.club.agents_balance == 0 

    agent.use_club()
    assert agent.club.user_balance == 200 
    assert agent.club.agents_balance == 0


    params = {'action': 'OUT', 'amount': 100}
    response = owner.post(f'/api/v1/clubs/{owner.club.id}/chips/players/{agent.user_id}', json=params)
    assert response.status_code == 201

    owner.use_club()
    assert owner.club.club_balance == 900 
    assert owner.club.user_balance == 0 
    assert owner.club.agents_balance == 0 

    agent.use_club()
    assert agent.club.user_balance == 100 
    assert agent.club.agents_balance == 0

