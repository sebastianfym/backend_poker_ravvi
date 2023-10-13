import logging
from typing import List, Mapping
from dataclasses import dataclass, asdict
import asyncio

from ..logging import ObjectLogger
from ..db import DBI
from .event import Event, TABLE_INFO, TABLE_CLOSED, PLAYER_ENTER, PLAYER_EXIT
from .client import Client
from .poker_nlh import NLH_subtype_factory
from .poker_plo import PLO_subtype_factory
from .user import User

class Table(ObjectLogger):
    NEW_GAME_DELAY = 7

    def __init__(self, id, *, table_type, table_seats, game_type, game_subtype, **kwargs):
        super().__init__(logger_name=__name__+f".{id}")
        self.table_id = id
        self.table_type = table_type
        self.game_type = game_type
        self.game_subtype = game_subtype
        if not table_seats:
            table_seats = 9
        if self.game_type=='PLO' and self.game_subtype=='PLO6':
            table_seats = min(table_seats, 6)
        self.seats : List[User] = [None]*table_seats
        self.dealer_idx = -1
        self.task : asyncio.Task = None
        self.clients : List[Client] = []
        self.game = None
        self.log_info("init: %s %s %s", self.game_type, self.game_subtype, len(self.seats))

    def get_user(self, user_id, *, connected=0):
        return User(id=user_id, username='u'+str(user_id), balance=1000, connected=connected)

    async def start(self):
        self.task = asyncio.create_task(self.run_wrappwer())

    async def stop(self):
        if not self.task:
            return
        if not self.task.done():
            self.task.cancel()
        await self.task
        self.task = None

    async def run_wrappwer(self):
        self.log_info("begin")
        try:
            await self.run_table()
        except asyncio.CancelledError:
            pass
        except Exception as ex:
            self.log_exception("%s", ex)
        finally:
            self.log_info("end")

    @property
    def take_seat_enabled(self):
        return True
    
    def on_user_seat_taken(self, user, user_seat_idx):
        pass

    async def run_table(self):
        raise NotImplementedError
    
    async def run_game(self, users, **game_props):
        with DBI() as db:
            row = db.game_begin(table_id=self.table_id, 
                                game_type=self.game_type, game_subtype=self.game_subtype,
                                user_ids=[u.id for u in users])
        try:
            game_factory = self.get_game_factory()
            if game_factory:
                self.game = game_factory(self, row.id, users, **game_props)
            if self.game:
                await self.game.run()
        finally:
            with DBI() as db:
                db.game_end(game_id=self.game.game_id)
            self.game = None


    async def remove_users(self, user_func):
        # remove users based on user_func(user) return
        for seat_idx, user in enumerate(self.seats):
            #self.log_debug("user_id=%s connected=%s", user.user_id, user.connected)
            if not user:
                continue
            if not user_func(user):
                continue
            self.seats[seat_idx] = None
            event = PLAYER_EXIT(table_id = self.table_id, user_id=user.id)
            await self.broadcast(event)
            self.log_info("user %s removed, seat %s available", user.id, seat_idx)


    def get_game_factory(self):
        if self.game_type=='NLH':
            return NLH_subtype_factory.get(self.game_subtype)
        if self.game_type=='PLO':
            return PLO_subtype_factory.get(self.game_subtype)
        return None
    

    async def send_TABLE_INFO(self, client):
        event = TABLE_INFO(table_id = self.table_id, table_redirect_id = self.table_id)
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
            players_info = []
            for p in self.game.players:
                if p.cards_open or p.user_id==client.user_id:
                    cards = p.cards
                else:
                    cards = [0 for _ in p.cards]
                u = users.get(p.user_id,None)
                if not u:
                    self.log_warning("user info %s not found", p.user_id)
                    continue
                u.update(
                    bet = p.bet_type,
                    amount = p.bet_amount,
                    cards = cards
                )
                players_info.append(p.user_id)
            banks_info = []
            banks = self.game.banks or []
            for b in banks:
                b_info = dict(amount = b[0])
                banks_info.append(b_info)
            event.update(
                game_id = self.game.game_id,
                game_type = self.game.GAME_TYPE,
                game_subtype = self.game.GAME_SUBTYPE,
                banks = banks_info,
                cards = self.game.cards,
                players = players_info,
                dealer_id = self.game.dealer_id,
                current_user_id = self.game.current_player.user_id
            )
        event.update(
            table_type = self.table_type,
            seats = [None if u is None else u.id for u in self.seats],
            users = list(users.values())
        )
        await client.send_event(event)

    async def add_client(self, client: Client, take_seat: bool):
        user = None
        user_seat_idx = None
        seats_available = []
        
        # check seats allocation
        for i, u in enumerate(self.seats):
            if u is None:
                seats_available.append(i)
            elif u.id == client.user_id:
                user = u
                user_seat_idx = i

        if user_seat_idx is None:
            # take a seat
            if take_seat and seats_available and self.take_seat_enabled:
                user = self.get_user(client.user_id)
                user_seat_idx = seats_available[0]
                self.seats[user_seat_idx] = user

        # user_seat_idx occupied by user
        if user:
            user.connected += 1
            client.tables.add(self.table_id)
            # in case of the first cleint connection
            if user.connected == 1:
                self.on_user_seat_taken(user, user_seat_idx)
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
        await self.send_TABLE_INFO(client)
        
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