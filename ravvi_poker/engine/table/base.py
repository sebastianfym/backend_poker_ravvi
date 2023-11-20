from typing import List, Mapping
import asyncio
import inspect

from ...logging import ObjectLogger
from ...db.adbi import DBI
from ..event import (
    Event,
    TABLE_INFO,
    TABLE_CLOSED,
    PLAYER_ENTER,
    PLAYER_SEAT,
    PLAYER_EXIT,
)
from ..user import User


class Table(ObjectLogger):
    DBI = DBI
    TABLE_TYPE = None

    NEW_GAME_DELAY = 3
    AFTER_GAME_DELAY = 3

    @classmethod
    def kwargs_keys(cls):
        keys = set()
        if cls.__base__ != ObjectLogger:
            keys.update(cls.__base__.kwargs_keys())
        spec = inspect.getfullargspec(cls)
        keys.update()
        if spec.kwonlyargs:
            keys.update(spec.kwonlyargs)
        if spec.kwonlydefaults:
            keys.update(spec.kwonlydefaults)
        return keys

    @classmethod
    def split_kwargs(cls, **kwargs):
        keys = cls.kwargs_keys()
        needed, other = {}, {}
        for k, v in kwargs.items():
            target = needed if k in keys else other
            target[k] = v
        return needed, other


    def __init__(self, id, parent_id=None, *, table_seats, club_id=None, game_type=None, game_subtype=None):
        super().__init__(logger_name=__name__)
        self.club_id = club_id
        self.table_id = id
        self.parent_id = parent_id
        self.table_seats = table_seats
        self.seats: List[User] = [None] * table_seats
        self.dealer_idx = -1
        self.users: Mapping[int, User] = {}
        self.task: asyncio.Task = None
        self.task_stop = False
        self.lock = asyncio.Lock()
        self.game_type = game_type
        self.game_subtype = game_subtype
        self.game = None

    def log_prefix(self):
        return f"{self.table_id}:"

    @property
    def table_type(self):
        return self.TABLE_TYPE
    
    @property
    def user_enter_enabled(self):
        raise NotImplementedError()

    @property
    def user_exit_enabled(self):
        raise NotImplementedError()

    async def user_factory(self, db, user_id):
        username='u'+str(user_id)
        return User(id=user_id, username=username)

    async def game_factory(self, users):
        raise NotImplementedError()

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

    async def on_user_join(self, db ,user):
        pass

    async def on_player_enter(self, db, user, seat_idx):
        user.balance = 1

    async def on_player_exit(self, db, user, seat_idx):
        # return table balance to user
        user.balance = 0

    async def on_user_leave(self, db, user):
        self.log_debug('on_user_leave(%s)', user.id if user else None)

    async def on_game_ended(self, db):
        self.log_debug('on_game_ended()')

    async def emit_event(self, db: DBI, event):
        event.update(table_id=self.table_id)
        self.log_debug('emit_event: %s', event)
        await db.emit_event(event)

    async def emit_TABLE_INFO(self, db, client_id, table_info):
        event = TABLE_INFO(client_id=client_id, **table_info)
        await self.emit_event(db, event)

    async def broadcast_TABLE_CLOSED(self, db):
        redirect_id = self.parent_id or self.table_id
        event = TABLE_CLOSED(table_redirect_id=redirect_id)
        await self.emit_event(db, event)

    async def broadcast_PLAYER_ENTER(self, db, user_info, seat_idx):
        event = PLAYER_ENTER(seat_id=seat_idx, user=user_info)
        await self.emit_event(db, event)

    async def broadcast_PLAYER_SEAT(self, db, user_id, seat_idx):
        event = PLAYER_SEAT(user_id=user_id, seat_id=seat_idx)
        await self.emit_event(db, event)

    async def broadcast_PLAYER_EXIT(self, db, user_id):
        event = PLAYER_EXIT(user_id=user_id)
        await self.emit_event(db, event)

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
    
    async def handle_cmd(self, db, user_id, client_id, cmd_type, kwargs):
        self.log_info("handle_cmd: %s/%s %s %s", user_id, client_id, cmd_type, kwargs)
        async with self.lock:
            if cmd_type == Event.CMD_TABLE_JOIN:
                take_seat = kwargs.get('take_seat', None)
                await self.handle_cmd_join(db, user_id, client_id, take_seat)
            elif cmd_type == Event.CMD_TAKE_SEAT:
                seat_idx = kwargs.get('seat_idx', None)
                await self.handle_cmd_take_seat(db, user_id, seat_idx)
            elif cmd_type == Event.CMD_TABLE_LEAVE:
                await self.handle_cmd_exit(db, user_id)
            elif self.game:
                await self.game.handle_cmd(db, user_id, cmd_type, kwargs)

    async def handle_cmd_join(self, db, user_id, client_id, take_seat):
        # check seats allocation
        user, seat_idx, seats_available = self.find_user(user_id)
        if not user:
            # init user object
            user = await self.user_factory(db, user_id)
        if not user.clients:
            await self.on_user_join(db, user)
        user.clients.add(client_id)
        # try to take a seat
        new_seat_idx, user_info = None, None
        if (
            seat_idx is None
            and take_seat
            and self.user_enter_enabled
            and seats_available
        ):
            new_seat_idx = seats_available[0]
            self.seats[new_seat_idx] = user
            await self.on_player_enter(db, user, new_seat_idx)
            # broadcast
            user_info = user.get_info()
            await self.broadcast_PLAYER_ENTER(db, user_info, new_seat_idx)
        # response
        table_info = self.get_table_info(user_id)
        await self.emit_TABLE_INFO(db, client_id, table_info)

    async def handle_cmd_take_seat(self, db, user_id: int, seat_idx: int):
        # check seats allocation
        user, old_seat_idx, seats_available = self.find_user(user_id)
        if not user:
            return False
        if seat_idx not in seats_available:
            return False
        if old_seat_idx is None:
            if not self.user_enter_enabled:
                return False
            self.seats[seat_idx] = user
            await self.on_player_enter(db, user, seat_idx)
            user_info = user.get_info()
            await self.broadcast_PLAYER_ENTER(db, user_info, seat_idx)         
        else:
            self.seats[old_seat_idx] = None
            self.seats[seat_idx] = user
            await self.broadcast_PLAYER_SEAT(db, user_id, seat_idx)
        return True

    async def handle_cmd_exit(self, db, user_id: int):
        if not self.user_exit_enabled:
            return False
        # check seats allocation
        user, seat_idx, _ = self.find_user(user_id)
        if not user or seat_idx is None:
            return
        self.seats[seat_idx] = None
        await self.on_player_exit(db, user, seat_idx)
        await self.broadcast_PLAYER_EXIT(db, user.id)

    async def handle_client_close(self, db, user_id, client_id):
        # check seats allocation
        user, seat_idx, _ = self.find_user(user_id)
        if not user or client_id not in user.clients:
            return
        user.clients.remove(client_id)
        if seat_idx is None and not user.connected:
            await self.on_user_leave(db, user)
            del self.users[user.id]

    async def start(self):
        self.log_info('start')
        self.task = asyncio.create_task(self.run_table_wrapper())
        self.log_info('started')

    async def stop(self):
        self.log_info('stop...')
        if not self.task:
            return
        if not self.task.done():
            self.task_stop = True
        try:
            await self.task
        except asyncio.CancelledError:
            pass
        self.task = None
        self.log_info('stopped')

    async def run_table_wrapper(self):
        self.log_info("begin")
        try:
            await self.run_table()
        except asyncio.CancelledError:
            pass
        except Exception as ex:
            self.log_exception("%s", ex)
        finally:
            self.log_info("end")

    async def sleep(self, delay: float):
        await asyncio.sleep(delay)

    async def run_table(self):
        while not self.task_stop:
            await self.sleep(self.NEW_GAME_DELAY)
            await self.run_game()
        
        #async with self.DBI() as db:
        #    await  db.close_table(self.table_id)
        #    await self.broadcast_TABLE_CLOSED(db)

    def user_can_play(self, user):
        return isinstance(user.balance, (int, float)) and user.balance>0
    
    def user_can_stay(self, user):
        if user.balance is None:
            return True
        return self.user_can_play(user)

    def get_game_players(self, *, min_size=2) -> List[User]:
        players = []
        for i, user in enumerate(self.seats):
            if user and self.user_can_play(user):
                players.append((i, user))
        if len(players) < min_size:
            return None
        max_idx, _ = players[-1]
        self.dealer_idx += 1
        if self.dealer_idx > max_idx:
            self.dealer_idx = 0
        while players[0][0] < self.dealer_idx:
            p = players.pop(0)
            players.append(p)
        self.dealer_idx = players[0][0]
        return [user for _, user in players]

    async def create_game(self, users):
        game = await self.game_factory(users)
        async with self.DBI() as db:
            row = await db.create_game(table_id=self.table_id,
                game_type=game.game_type, game_subtype=game.game_subtype, game_props=game.game_props,
                users=users,
            )
            game.game_id = row.id
        return game
    
    async def close_game(self, game):
        users = [p.user for p in game.players]
        async with self.DBI() as db:
            await db.close_game(game_id=self.game.game_id, users=users)

    async def remove_users(self, db):
        # remove users based on user_can_stay return
        for seat_idx, user in enumerate(self.seats):
            if not user:
                continue
            if self.user_can_stay(user):
                continue
            self.seats[seat_idx] = None
            self.on_player_exit(db, user, seat_idx)
            await self.broadcast_PLAYER_EXIT(db, user.id)
            self.log_info("user %s removed, seat %s available", user.id, seat_idx)
            if not user.connected:
                await self.on_user_leave(db, user)
                del self.users[user.id]
    
    async def run_game(self):
        async with self.lock:
            users = self.get_game_players()
            if not users:
                return
            self.game = await self.create_game(users)

        try:
            await self.game.run()
        except Exception as e:
            self.log_exception("%s", str(e))

        async with self.lock:
            await self.close_game(self.game)
            self.game = None