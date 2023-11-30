from typing import List, Mapping
import asyncio
import inspect
import contextlib

from ...logging import getLogger, ObjectLoggerAdapter
from ...db import DBI
from ..user import User
from ..events import Command, Message

logger = getLogger(__name__)


class Table:
    DBI = DBI
    TABLE_TYPE = None

    NEW_GAME_DELAY = 3

    def __init__(self, id, *, table_seats, parent_id=None, club_id=None, game_type=None, game_subtype=None, props=None, **kwargs):
        self.table_id = id
        self.log = ObjectLoggerAdapter(logger, lambda: self.table_id)
        self.parent_id = parent_id
        self.club_id = club_id
        self.table_seats = table_seats
        self.seats: List[User] = [None] * table_seats
        self.dealer_idx = -1
        self.users: Mapping[int, User] = {}
        self.task: asyncio.Task = None
        self.task_stop = False
        self.lock = asyncio.Lock()
        self.game_type = game_type
        self.game_subtype = game_subtype
        self.game_props = {}
        self.game = None
        self.log.info("props: %s", props)
        self.parse_props(**(props or {}))

    def parse_props(self, **kwargs):
        pass

    @property
    def table_type(self):
        return self.TABLE_TYPE

    @property
    def user_enter_enabled(self):
        return True

    @property
    def user_exit_enabled(self):
        return True

    async def user_factory(self, db, user_id):
        user = await db.get_user(user_id)
        return User(id=user.id, username=user.username)

    async def game_factory(self, users):
        from ..game import get_game_class
        for u in users:
            self.log.info("user(%s, %s)", u.id, u.balance)
        self.log.info("game_factory(%s, %s, %s)", self.game_type, self.game_subtype, self.game_props)
        game_class = get_game_class(self.game_type, self.game_subtype)
        return game_class(self, users, **self.game_props)

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

    async def on_user_join(self, db, user):
        pass

    async def on_player_enter(self, db, user, seat_idx):
        # TODO buyin
        user.balance = 1
        return True

    async def on_player_exit(self, db, user, seat_idx):
        # TODO return table balance to user
        user.balance = None

    async def on_user_leave(self, db, user):
        self.log.debug("on_user_leave(%s)", user.id if user else None)

    async def on_game_end(self, db):
        self.log.debug("on_game_ended()")

    async def emit_msg(self, db: DBI, msg: Message):
        msg.update(table_id=self.table_id)
        self.log.debug("emit_msg: %s", msg)
        await db.create_table_msg(**msg)

    async def emit_TABLE_INFO(self, db, *, cmd_id, client_id, table_info):
        msg = Message(msg_type=Message.Type.TABLE_INFO, cmd_id=cmd_id, client_id=client_id, **table_info)
        await self.emit_msg(db, msg)

    async def broadcast_TABLE_NEXT_LEVEL_INFO(self, db, **kwargs):
        msg = Message(msg_type=Message.Type.TABLE_NEXT_LEVEL_INFO, **kwargs)
        await self.emit_msg(db, msg)

    async def broadcast_TABLE_CLOSED(self, db):
        redirect_id = self.parent_id or self.table_id
        msg = Message(msg_type=Message.Type.TABLE_CLOSED, table_redirect_id=redirect_id)
        await self.emit_msg(db, msg)

    async def broadcast_PLAYER_ENTER(self, db, user_info, seat_idx):
        msg = Message(msg_type=Message.Type.PLAYER_ENTER, seat_id=seat_idx, user=user_info)
        await self.emit_msg(db, msg)

    async def broadcast_PLAYER_SEAT(self, db, user_id, seat_idx):
        msg = Message(msg_type=Message.Type.PLAYER_SEAT, user_id=user_id, seat_id=seat_idx)
        await self.emit_msg(db, msg)

    async def broadcast_PLAYER_EXIT(self, db, user_id):
        msg = Message(msg_type=Message.Type.PLAYER_EXIT, user_id=user_id)
        await self.emit_msg(db, msg)

    def get_table_info(self, user_id):
        users_info = {u.id: u.get_info() for u in self.seats if u is not None}
        result = dict(
            table_id=self.table_id,
            table_redirect_id=self.table_id,
            table_type=self.table_type,
            seats=[None if u is None else u.id for u in self.seats]
        )
        if self.game:
            game_info = self.game.get_info(user_id=user_id, users_info=users_info)
            result.update(game_info)
        result.update(users=list(users_info.values()))
        return result

    async def handle_cmd(self, db, *, cmd_id:int, cmd_type: int, user_id:int, client_id:int, props: dict):
        cmd_type = Command.Type.decode(cmd_type)
        self.log.info("handle_cmd: %s/%s %s %s", user_id, client_id, cmd_type, props)
        async with self.lock:
            if cmd_type == Command.Type.JOIN:
                take_seat = props.get("take_seat", None)
                await self.handle_cmd_join(db, cmd_id=cmd_id, client_id=client_id, user_id=user_id, take_seat=take_seat)
            elif cmd_type == Command.Type.TAKE_SEAT:
                seat_idx = props.get("seat_idx", None)
                await self.handle_cmd_take_seat(db, user_id=user_id, seat_idx=seat_idx)
            elif cmd_type == Command.Type.EXIT:
                await self.handle_cmd_exit(db, user_id=user_id)
            elif self.game:
                await self.game.handle_cmd(db, user_id=user_id, cmd_type=cmd_type, props=props)
            else:
                self.log.warning("handle_cmd: unknown cmd_type = %s", cmd_type)

    async def handle_cmd_join(self, db, *, cmd_id, client_id, user_id, take_seat):
        # check seats allocation
        user, seat_idx, seats_available = self.find_user(user_id)
        if not user:
            # init user object
            user = await self.user_factory(db, user_id)
            self.users[user_id] = user
        if not user.clients:
            await self.on_user_join(db, user)
        user.clients.add(client_id)
        # try to take a seat
        new_seat_idx, user_info = None, None
        if seat_idx is None and take_seat and self.user_enter_enabled and seats_available:
            # allocate seat
            new_seat_idx = seats_available.pop(0)
            # check user can take seat
            if await self.on_player_enter(db, user, new_seat_idx):
                self.seats[new_seat_idx] = user
                user_info = user.get_info()
                await self.broadcast_PLAYER_ENTER(db, user_info, new_seat_idx)
        # response
        table_info = self.get_table_info(user_id)
        await self.emit_TABLE_INFO(db, cmd_id=cmd_id, client_id=client_id, table_info=table_info)

    async def handle_cmd_take_seat(self, db, *, user_id: int, seat_idx: int):
        # check seats allocation
        user, old_seat_idx, seats_available = self.find_user(user_id)
        if not user:
            return False
        if seat_idx not in seats_available:
            return False
        if old_seat_idx is None:
            if not self.user_enter_enabled:
                return False
            if not await self.on_player_enter(db, user, seat_idx):
                return False
            self.seats[seat_idx] = user
            user_info = user.get_info()
            await self.broadcast_PLAYER_ENTER(db, user_info, seat_idx)
        else:
            self.seats[old_seat_idx] = None
            self.seats[seat_idx] = user
            await self.broadcast_PLAYER_SEAT(db, user_id, seat_idx)
        return True

    async def handle_cmd_exit(self, db, *, user_id: int):
        if not self.user_exit_enabled:
            return False
        # check seats allocation
        user, seat_idx, _ = self.find_user(user_id)
        if not user or seat_idx is None:
            return False
        self.seats[seat_idx] = None
        await self.on_player_exit(db, user, seat_idx)
        await self.broadcast_PLAYER_EXIT(db, user.id)
        return True

    async def handle_client_close(self, db, *, user_id, client_id):
        # check seats allocation
        user, seat_idx, _ = self.find_user(user_id)
        if not user or client_id not in user.clients:
            return
        user.clients.remove(client_id)
        if seat_idx is None and not user.connected:
            await self.on_user_leave(db, user)
            del self.users[user.id]

    async def start(self):
        self.log.debug("start")
        self.task = asyncio.create_task(self.run_table_wrapper())
        self.log.info("started")

    async def stop(self):
        self.log.debug("stop...")
        if not self.task:
            return
        self.task_stop = True
        with contextlib.suppress(asyncio.exceptions.CancelledError):
            await self.task
        self.task = None
        self.log.info("stopped")

    async def run_table_wrapper(self):
        self.log.info("begin")
        try:
            await self.run_table()
        except asyncio.CancelledError:
            pass
        except Exception as ex:
            self.log.exception("%s", ex)
        finally:
            self.log.info("end")

    async def sleep(self, delay: float):
        await asyncio.sleep(delay)

    async def run_table(self):
        while not self.task_stop:
            await self.sleep(self.NEW_GAME_DELAY)
            await self.run_game()
            async with self.lock:
                async with self.DBI() as db:
                    await self.remove_users(db)
        async with self.lock:
            async with self.DBI() as db:
                await self.remove_users(db, force=True)
        # async with self.DBI() as db:
        #    await  db.close_table(self.table_id)
        #    await self.broadcast_TABLE_CLOSED(db)

    def user_can_play(self, user):
        return isinstance(user.balance, (int, float)) and user.balance > 0

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
            row = await db.create_game(
                table_id=self.table_id,
                game_type=game.game_type,
                game_subtype=game.game_subtype,
                props=game.game_props,
                players=users,
            )
            game.game_id = row.id
        return game

    async def close_game(self, game):
        users = [p.user for p in game.players]
        async with self.DBI() as db:
            await db.close_game(self.game.game_id, players=users)

    async def remove_users(self, db, force=False):
        # remove users based on user_can_stay return
        for seat_idx, user in enumerate(self.seats):
            if not user:
                continue
            if not force and self.user_can_stay(user):
                continue
            self.seats[seat_idx] = None
            await self.on_player_exit(db, user, seat_idx)
            await self.broadcast_PLAYER_EXIT(db, user.id)
            self.log.info("user %s removed, seat %s available", user.id, seat_idx)
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
            self.log.exception("%s", str(e))

        async with self.lock:
            await self.close_game(self.game)
            self.game = None
