from typing import List
from .client import Client    

class Table:

    def __init__(self, n_seats=9):
        self.table_id = None
        self.seats = [None]*n_seats
        self.dealer_idx = -1
        self.clients : List[Client] = []
        self.game = None

    async def add_client(self, client, join):
        self.clients.append(client)
        # send table info
        if not join:
            return False
        seats_available = [i for i, s in enumerate(self.seats) if s is None]
        if not seats_available:
            return False
        idx = seats_available[0]
        self.seats[idx] = client
        # broadcast SEAT event
        return True
    
    def broadcast(self, event):
        event.update(table_id=self.table_id)
        for client in self.clients:
            client.send(event)

    def get_players(self, min_size):
        players = [(i, p) for i, p in enumerate(self.seats) if p is not None]
        if len(players)<min_size:
            return None
        max_idx = players[-1][0]
        self.dealer_idx += 1
        if self.dealer_idx>max_idx:
            self.dealer_idx = 0
        while players[0][0]<self.dealer_idx:
            p = players.pop(0)
            players.append(p)
        self.dealer_idx = players[0][0]
        return [p for i, p in players]

