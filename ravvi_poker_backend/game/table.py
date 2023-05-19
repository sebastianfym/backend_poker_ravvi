from typing import List, Mapping
from dataclasses import dataclass, asdict
import asyncio
from asyncio import Task
from .event import Event, TABLE_INFO, PLAYER_ENTER
from .client import Client
from .game import Game
from .user import User

class Table:

    def __init__(self, n_seats=9):
        self.table_id = None
        self.task : asyncio.Task = None
        self.clients : List[Client] = []
        self.users = {}
        self.seats = [None]*n_seats
        self.dealer_idx = -1
        self.game = None

    async def start(self):
        self.task = asyncio.create_task(self.run())

    async def stop(self):
        if not self.task:
            return
        if not self.task.done():
            self.task.cancel()
        await self.task
        self.task = None

    async def run(self):
        try:
            while True:
                users = self.get_players(3)
                if users:
                    self.game = Game(users)
                    self.game.table = self
                    await self.game.run()
                    self.game = None
                await asyncio.sleep(5)
        except asyncio.CancelledError:
            pass

    def add_user(self, user_id):
        user = self.users.get(user_id, None)
        if not user:
            user = User(
                user_id=user_id,
                username='u'+str(user_id),
                balance=1000
                )
            self.users[user_id] = user
        return user

    def get_info(self, target_user_id=None):
        info = TABLE_INFO(
            table_id = self.table_id,
        )
        users = {}
        for user_id in self.seats:
            if not user_id:
                continue
            u = self.users.get(user_id)
            users[user_id] = dict(
                    user_id = u.user_id,
                    username = u.username,
                    balance = u.balance
                )
        if self.game:
            players = []
            for p in self.game.players:
                if p.cards_open or p.user_id==target_user_id:
                    cards = p.cards
                else:
                    cards = [0 for _ in p.cards]
                u = users.get(p.user_id,None)
                u.update(
                    bet = p.bet_type,
                    amount = p.bet_amount,
                    cards = cards
                )
                players.append(p.user_id)
            info.update(
                game_id = self.game.game_id,
                bank_amount = self.game.bank,
                cards = self.game.cards,
                players = players,
                dealer_id = self.game.dealer_id,
                current_user_id = self.game.current_player.user_id
            )
        info.update(
            seats = list(self.seats),
            users = list(users.values())
        )
        return info

    async def add_client(self, client: Client, join):
        # send current table stage to client
        info = self.get_info(client.user_id)
        await client.send(info)
        # register
        self.clients.append(client)
        if not join:
            return False
        seats_available = [i for i, user_id in enumerate(self.seats) if user_id is None]
        if not seats_available:
            return False
        user = self.add_user(client.user_id)
        idx = seats_available[0]
        self.seats[idx] = client.user_id
        # broadcast PLAYER_ENTER event
        event = PLAYER_ENTER(
            table_id = self.table_id,
            seat_id = idx,
            user = user.asdict()
        )
        await self.broadcast(event)
        return True
    
    async def remove_client(self, client):
        try:
            self.clients.remove(client)
            for i, s in enumerate(self.seats):
                if s==client.user_id:
                    self.seats[i] = None
        except ValueError:
            pass
    
    async def handle_command(self, command: Event):
        if command.type == Event.CMD_PLAYER_BET and self.game:
            p = self.game.current_player
            if command.user_id == p.user_id:
                self.game.handle_bet(command.user_id, command.bet, command.amount)

    async def broadcast(self, event: Event):
        event.update(table_id=self.table_id)
        for client in self.clients:
            await client.send(event)

    def get_players(self, min_size):
        players = [(i, user_id) for i, user_id in enumerate(self.seats) if user_id is not None]
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
        return [self.users[user_id] for _, user_id in players]
