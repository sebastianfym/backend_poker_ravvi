from typing import List, Mapping
import asyncio

from ..logging import ObjectLogger
from ..db.adbi import DBI
from ..game.event import (
    Event,
    TABLE_INFO,
    TABLE_CLOSED,
    PLAYER_ENTER,
    PLAYER_SEAT,
    PLAYER_EXIT,
)
from ..game.poker_nlh import NLH_subtype_factory
from ..game.poker_plo import PLO_subtype_factory
from .user import User


class Table(ObjectLogger):
    TABLE_TYPE = None

    NEW_GAME_DELAY = 3

    def __init__(
        self,
        id,
        *,
        table_seats,
        club_id=None,
        **kwargs,
    ):
        super().__init__(logger_name=__name__)
        self.manager = None
        self.club_id = club_id
        self.table_id = id
        self.table_seats = table_seats
        self.seats: List[User] = [None] * table_seats
        self.dealer_idx = -1
        self.users: Mapping[int, User] = {}
        self.task: asyncio.Task = None
        self.lock = asyncio.Lock()
        self.game = None

    def log_prefix(self):
        return f" {self.table_id}: "

    @property
    def table_type(self):
        return self.TABLE_TYPE
    
    @property
    def take_seat_enabled(self):
        raise NotImplementedError

    async def user_factory(self, user_id):
        raise NotImplementedError

    async def game_factory(self):
        raise NotImplementedError

    def find_user(self, user_id):
        user, seat_idx = None, None
        seats_available = []
        for i, u in enumerate(self.seats):
            if u is None:
                seats_available.append(i)
            elif u.id == user_id:
                user = u
                seat_idx = i
        if not user:
            user = self.users.get(user_id, None)
        return user, seat_idx, seats_available

    async def on_user_join(self, user):
        raise NotImplementedError

    async def on_player_enter(self, user, seat_idx):
        raise NotImplementedError

    async def on_player_exit(self, user, seat_idx):
        raise NotImplementedError

    async def on_user_leave(self, user):
        raise NotImplementedError

    async def emit_event(self, event):
        raise NotImplementedError

    async def emit_TABLE_INFO(self, client_id, table_info):
        event = TABLE_INFO(client_id=client_id, **table_info)
        await self.emit_event(event)

    async def broadcast_PLAYER_ENTER(self, seat_idx, user_info):
        event = PLAYER_ENTER(seat_id=seat_idx, user=user_info)
        await self.emit_event(event)

    async def broadcast_PLAYER_SEAT(self, user_id, seat_idx):
        event = PLAYER_SEAT(user_id=user_id, seat_id=seat_idx)
        await self.emit_event(event)

    def get_table_info(self, user_id):
        users = {u.id: u.get_info() for u in self.seats if u is not None}
        result = dict(
            table_id=self.table_id,
            table_redirect_id=self.table_id,
            table_type=self.table_type,
            seats=[None if u is None else u.id for u in self.seats],
            users=users,
        )
        if self.game:
            game_info = self.game.get_info(users=users, client_user_id=user_id)
            result.update(game_info)
        return result

    async def handle_cmd_join(self, user_id, client_id, take_seat):
        async with self.lock:
            # check seats allocation
            user, seat_idx, seats_available = self.find_user(user_id)
            if not user:
                # init user object
                user = await self.user_factory(user_id)
                await self.on_user_join(user)
            # register client
            user.clients.add(client_id)
            # try to take a seat
            new_seat_idx, user_info = None, None
            if (
                seat_idx is None
                and take_seat
                and self.take_seat_enabled
                and seats_available
            ):
                new_seat_idx = seats_available[0]
                self.seats[new_seat_idx] = user
                await self.on_player_enter(user, new_seat_idx)
                user_info = user.get_info()
            # info for events
            table_info = self.get_table_info(user_id)

        # emit events
        if new_seat_idx and user_info:
            await self.broadcast_PLAYER_ENTER(new_seat_idx, user_info)
        await self.emit_TABLE_INFO(client_id, table_info)

    async def handle_cmd_take_seat(self, user_id: int, new_seat_idx: int):
        async with self.lock:
            # check seats allocation
            user, seat_idx, seats_available = self.find_user(user_id)
            if not user:
                return
            if new_seat_idx not in seats_available:
                return
            if seat_idx:
                self.seats[seat_idx] = None
            self.seats[new_seat_idx] = user
            user_info = user.get_info()
        if not seat_idx:
            await self.broadcast_PLAYER_ENTER(new_seat_idx, user_info)
        else:
            await self.broadcast_PLAYER_SEAT(user_id, new_seat_idx)

    async def handle_cmd_leave(self, user_id, client_id):
        async with self.lock:
            # check seats allocation
            user, seat_idx, _ = self.find_user(user_id)
            if not user:
                return
            if client_id in user.clients:
                user.clients.remove(client_id)
            if seat_idx is None:
                if not user.clients:
                    del self.users[user_id]
                    await self.on_user_leave(user)

    async def start(self):
        self.task = asyncio.create_task(self.run_wrappwer())

    async def stop(self):
        if not self.task:
            return
        if not self.task.done():
            self.task.cancel()
        try:
            await self.task
        except asyncio.CancelledError:
            pass
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

    async def run_table(self):
        raise NotImplementedError

    def get_game_players(self, *, min_size=2, exclude_offile=True) -> List[User]:
        players = []
        for i, user in enumerate(self.seats):
            if user is None:
                continue
            if exclude_offile and not user.connected:
                continue
            players.append((i, user))
        if len(players) < min_size:
            return None
        max_idx = players[-1][0]
        self.dealer_idx += 1
        if self.dealer_idx > max_idx:
            self.dealer_idx = 0
        while players[0][0] < self.dealer_idx:
            p = players.pop(0)
            players.append(p)
        self.dealer_idx = players[0][0]
        return [user for _, user in players]

    async def game_begin(self, users, **kwargs):
        from .game import Game
        game: Game = self.game_factory(**kwargs)
        async with DBI() as db:
            row = db.game_begin(table_id=self.table_id,
                game_type=self.game_type, game_subtype=self.game_subtype, game_props=game.game_props,
                users=users,
            )
            game.game_id = row.id
        return game
    
    async def game_end(self, game):
        users = [p.user for p in game.players]
        async with DBI() as db:
            db.game_end(game_id=self.game.game_id, users=users)

    async def run_game(self, users, **kwargs):
        try:
            self.game = self.game_factory(**kwargs)
            async with DBI() as db:
                row = db.game_begin(
                    table_id=self.table_id,
                    game_type=self.game_type,
                    game_subtype=self.game_subtype,
                    users=users,
                )
            await self.game.run()
            async with DBI() as db:
                db.game_end(game_id=self.game.game_id, users=users)
        except Exception as ex:
            self.log_exception("%s", ex)
        finally:
            self.game = None
