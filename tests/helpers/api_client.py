from typing import Any, Dict
from fastapi.testclient import TestClient
from ravvi_poker.api.app import app
from ravvi_poker.api.auth.types import UserAccessProfile
from ravvi_poker.api.clubs.types import ClubProfile
from ravvi_poker.api.chips.txns_club import ClubTxnHistory

class APITestClient(TestClient):
    def __init__(self) -> None:
        super().__init__(app)
        self.profile = None
        self.club = None

    @property
    def user_id(self):
        return self.profile.user.id

    def register(self):
        params = dict(device_token=None, device_props={})
        response = self.post("/api/v1/auth/register", json=params)
        assert response.status_code == 200
        self.profile = UserAccessProfile(**response.json())
        self.headers = {"Authorization": "Bearer " + self.profile.access_token}

    def create_club(self):
        response = self.post("/api/v1/clubs", json={})
        assert response.status_code == 201
        self.club = ClubProfile(**response.json())

    def use_club(self, club_id=None):
        club_id = club_id or self.club.id
        response = self.get(f"/api/v1/clubs/{club_id}")
        assert response.status_code == 200
        self.club = ClubProfile(**response.json())

    def join_club(self):
        response = self.post(f"/api/v1/clubs/{self.club.id}/members", json={})
        assert response.status_code == 200
        self.club = ClubProfile(**response.json())

    def club_chips(self, detla):
        params = {
            'action': 'IN' if detla>0 else 'out', 
            'amount': abs(detla)}
        response = self.post(f'/api/v1/clubs/{self.club.id}/chips', json=params)
        assert response.status_code == 201

    def get_txns_club(self):
        response = self.get(f"/api/v1/clubs/{self.club.id}/txns/club")
        assert response.status_code == 200
        data = ClubTxnHistory(**response.json())
        return data

    def get_txns_player(self):
        response = self.get(f"/api/v1/clubs/{self.club.id}/txns/player")
        assert response.status_code == 200
        data = ClubTxnHistory(**response.json())
        return data

    def approve_member(self, user_id, **kwargs):
        response = self.put(f"/api/v1/clubs/{self.club.id}/members/{user_id}", json=kwargs)
        assert response.status_code == 200


    
