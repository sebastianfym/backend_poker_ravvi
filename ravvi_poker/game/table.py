import logging
from typing import List, Mapping
from dataclasses import dataclass, asdict
import asyncio

from ..logging import ObjectLogger
from ..db import DBI
from .event import Event, TABLE_INFO, PLAYER_ENTER, PLAYER_EXIT
from .client import Client
from .game import Game
from .user import User

class Table(ObjectLogger):
    NEW_GAME_DELAY = 7

    def __init__(self, table_id, n_seats=9):
        super().__init__(logger_name=__name__+f".{table_id}")
        self.table_id = table_id
        self.seats : List[User] = [None]*n_seats
        self.dealer_idx = -1
        self.task : asyncio.Task = None
        self.clients : List[Client] = []
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
        self.log_info("begin")
        try:
            while True:
                await asyncio.sleep(self.NEW_GAME_DELAY)
                # try to start new game
                users = self.get_players(2)
                if users:
                    # ok to start
                    with DBI() as db:
                        row = db.game_begin(table_id=self.table_id, user_ids=[u.id for u in users])
                    self.game = Game(self, row.id, users)
                    await self.game.run()
                    with DBI() as db:
                        row = db.game_end(game_id=self.game.game_id)
                    self.game = None
              
                await asyncio.sleep(2)
                # remove diconnected users
                for seat_idx, user in enumerate(self.seats):
                    #self.log_debug("user_id=%s connected=%s", user.user_id, user.connected)
                    if not user:
                        continue
                    if user.connected:
                        continue
                    self.seats[seat_idx] = None
                    event = PLAYER_EXIT(table_id = self.table_id, user_id=user.id)
                    await self.broadcast(event)
                    self.log_info("user %s removed, seat %s available", user.id, seat_idx)
                   

        except asyncio.CancelledError:
            pass
        except Exception as ex:
            self.log_exception("%s", ex)
        finally:
            self.log_info("end")

    def get_info(self, target_user_id):
        info = TABLE_INFO(
            table_id = self.table_id,
        )
        users = {}
        for user in self.seats:
            if not user:
                continue
            users[user.id] = dict(
                    user_id = user.id,
                    username = user.username,
                    balance = user.balance
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
            seats = [None if u is None else u.id for u in self.seats],
            users = list(users.values())
        )
        return info

    def get_user(self, user_id, *, connected=0):
        return User(id=user_id, username='u'+str(user_id), balance=1000, connected=connected)

    async def add_client(self, client: Client, take_seat: bool):
        user = None
        user_seat_idx = None
        if take_seat:
            # check seats allocation
            seats_available = []
            for i, u in enumerate(self.seats):
                if u is None:
                    seats_available.append(i)
                elif u.id == client.user_id:
                    user = u
                    user_seat_idx = i

            # take a seat
            if user_seat_idx is None and seats_available:
                user = self.get_user(client.user_id)
                user_seat_idx = seats_available[0]
                self.seats[user_seat_idx] = user

            # user_seat_idx occupied by user
            if user:
                user.connected += 1
                client.tables.add(self.table_id)
                # in case of the first cleint connection
                if user.connected == 1:
                    # broadcast PLAYER_ENTER event
                    event = PLAYER_ENTER(
                        table_id = self.table_id,
                        seat_id = user_seat_idx,
                        user = dict(
                            user_id = user.id, username = user.username, balance=user.balance
                        )
                    )
                    await self.broadcast(event)

        # send current table info to client (including above seat taken)
        info = self.get_info(client.user_id)
        self.log_debug("%s", info)
        await client.send_event(info)
        
        # register client
        if client not in self.clients:
            self.clients.append(client)
        return user_seat_idx
    
    async def remove_client(self, client):
        # find user in seats
        user = None
        for i, u in enumerate(self.seats):
            if u is None:
                pass
            elif u.id == client.user_id:
                user = u
        if self.table_id in client.tables:
            client.tables.remove(self.table_id)
            if user:
                user.connected -= 1
                self.log_info("client %s removed, user(%s).connected=%s", client.client_id, user.id, user.connected)
            else:
                self.log_info("client %s removed, no user found", client.client_id)
        if client in self.clients:
            self.clients.remove(client)
    
    async def handle_command(self, client: Client, command: Event):
        if command.type == Event.CMD_TABLE_JOIN:
            self.save_event(command.type, client.user_id, command)
            await self.add_client(client, command.take_seat)
        elif command.type == Event.CMD_TABLE_LEAVE:
            await self.remove_client(client)
        elif command.type == Event.CMD_PLAYER_BET:
            if self.game:
                self.save_event(command.type, client.user_id, command)
                self.game.handle_bet(client.user_id, command.bet, command.amount)
        else:
            raise ValueError('Invalid command')
        
    async def broadcast(self, event: Event):
        self.log_info("broadcast: %s", event)
        if event.type not in [Event.GAME_BEGIN]:
            self.save_event(event.type, None, event)
        event.update(table_id=self.table_id)
        for client in self.clients:
            await client.send_event(event)

    def save_event(self, type, user_id, props):
        with DBI() as db:
            db.save_event(
                type=type,
                table_id=self.table_id, 
                game_id= self.game.game_id if self.game else None,
                user_id=user_id,
                props=props
            )

    def get_players(self, min_size) -> List[User]:
        players = []
        for i, user in enumerate(self.seats):
            if user is None:
                continue
            if not user.connected:
                continue
            players.append((i, user))
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
        return [user for _, user in players]
