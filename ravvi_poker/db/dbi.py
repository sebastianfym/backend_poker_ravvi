import datetime
import logging
import os
import json
import base64
import psycopg
import psycopg_pool
from psycopg.rows import namedtuple_row, dict_row
from psycopg.connection import Notify

logger = logging.getLogger(__name__)


class DBI:
    DB_HOST = os.getenv("RAVVI_POKER_DB_HOST", "localhost")
    DB_PORT = int(os.getenv("RAVVI_POKER_DB_PORT", "15432"))
    DB_NAME = os.getenv("RAVVI_POKER_DB_NAME", "develop")
    DB_USER = os.getenv("RAVVI_POKER_DB_USER", "postgres")
    DB_PASSWORD = os.getenv("RAVVI_POKER_DB_PASSWORD", "password")
    APPLICATION_NAME = 'CPS'
    CONNECT_TIMEOUT = 15

    pool = None

    OperationalError = psycopg.OperationalError
    PoolTimeout = psycopg_pool.PoolTimeout
    ForeignKeyViolation = psycopg.errors.ForeignKeyViolation

    @classmethod
    def conninfo(cls, db_name: str | None = None):
        conninfo = psycopg.conninfo.make_conninfo(
            host=cls.DB_HOST,
            port=cls.DB_PORT,
            dbname=db_name or cls.DB_NAME,
            user=cls.DB_USER,
            password=cls.DB_PASSWORD,
            connect_timeout=cls.CONNECT_TIMEOUT,
            application_name=cls.APPLICATION_NAME,
        )
        return conninfo

    @classmethod
    async def pool_open(cls):
        cls.pool = psycopg_pool.AsyncConnectionPool(conninfo=cls.conninfo(), open=False)
        await cls.pool.open()
        logger.debug("pool: ready")

    @classmethod
    async def pool_close(cls):
        await cls.pool.close()
        cls.pool = None
        logger.debug("pool: closed")

    def __init__(self, *, log=None, use_pool=True) -> None:
        self.log = log or logger
        self.dbi_pool = self.pool if use_pool else None
        self.dbi = None

    async def connect(self):
        if self.dbi_pool:
            self.dbi = await self.dbi_pool.getconn(timeout=self.CONNECT_TIMEOUT)
        else:
            self.dbi = await psycopg.AsyncConnection.connect(self.conninfo())

    async def close(self):
        if self.dbi_pool:
            await self.dbi_pool.putconn(self.dbi)
        else:
            await self.dbi.close()
        self.dbi = None

    def transaction(self):
        return self.dbi.transaction()

    async def commit(self):
        await self.dbi.commit()

    async def rollback(self):
        await self.dbi.rollback()

    def cursor(self, *args, row_factory=namedtuple_row, **kwargs):
        return self.dbi.cursor(*args, row_factory=row_factory, **kwargs)

    async def get_pg_backend_pid(self):
        async with self.cursor() as cursor:
            await cursor.execute("select pg_backend_pid() as pg_backend_pid")
            row = await cursor.fetchone()
        return row.pg_backend_pid

    # CONTEXT

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()
            self.dbi_pool = None
        await self.close()

    def use_id_or_uuid(self, id, uuid):
        if id is not None:
            key, value = "id", id
        elif uuid is not None:
            key, value = "uuid", uuid
        else:
            raise ValueError("login: id or uuid required")
        return key, value

    async def listen(self, channel):
        await self.dbi.execute(f"LISTEN {channel}")

    async def unlisten(self, channel):
        await self.dbi.execute(f"UNLISTEN {channel}")

    # DEVICE

    async def create_device(self, props=None):
        props = json.dumps(props) if props else None
        sql = "INSERT INTO user_device (props) VALUES (%s) RETURNING *"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (props,))
            row = await cursor.fetchone()
        return row

    async def get_device(self, id=None, *, uuid=None):
        key, value = self.use_id_or_uuid(id, uuid)
        sql = f"SELECT * FROM user_device WHERE {key}=%s"  # nosec
        async with self.cursor() as cursor:
            await cursor.execute(sql, (value,))
            row = await cursor.fetchone()
        return row

    # USER

    async def create_user(self, *, balance=1000):
        sql = "INSERT INTO user_profile (name) VALUES (NULL) RETURNING *"
        async with self.cursor() as cursor:
            await cursor.execute(sql)
            user = await cursor.fetchone()
        # default LOBBY account
        sql = "INSERT INTO user_account (user_id, balance, approved_ts, approved_by) VALUES (%s,%s,now_utc(),0) RETURNING *"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (user.id, balance))
            account = await cursor.fetchone()
        # registration reward
        sql = "INSERT INTO user_account_txn (account_id, txn_type, txn_value) VALUES (%s,'REGISTER',%s) RETURNING *"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (account.id, balance))
            txn = await cursor.fetchone()
        return user

    async def get_user(self, id=None, *, uuid=None):
        key, value = self.use_id_or_uuid(id, uuid)
        sql = f"SELECT * FROM user_profile WHERE {key}=%s"  # nosec
        async with self.cursor() as cursor:
            await cursor.execute(sql, (value,))
            row = await cursor.fetchone()
        return row

    async def update_user(self, id, **kwargs):
        if kwargs:
            params = ", ".join([f"{key}=%s" for key in kwargs])
            values = list(kwargs.values()) + [id]
            sql = f"UPDATE user_profile SET {params} WHERE id=%s RETURNING *"
        else:
            values = [id]
            sql = "SELECT * FROM user_profile WHERE id=%s"
        async with self.cursor() as cursor:
            await cursor.execute(sql, values)
            row = await cursor.fetchone()
        return row

    async def update_user_password(self, id, password_hash):
        sql = "UPDATE user_profile SET password_hash=%s WHERE id=%s"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (password_hash, id))

    async def close_user(self, id=None, *, uuid=None):
        key, value = self.use_id_or_uuid(id, uuid)
        sql = f"UPDATE user_profile SET closed_ts=now_utc() WHERE {key}=%s RETURNING *"  # nosec
        async with self.cursor() as cursor:
            await cursor.execute(sql, (value,))
            row = await cursor.fetchone()
        return row

    async def get_user_image(self, user_id):
        sql = "SELECT image_id FROM user_profile WHERE id=%s"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (user_id,))
            row = await cursor.fetchone()
        return row

    # LOGIN

    async def create_login(self, device_id, user_id):
        sql = "INSERT INTO user_login (device_id, user_id) VALUES (%s, %s) RETURNING *"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (device_id, user_id))
            row = await cursor.fetchone()
        return row

    async def get_login(self, id=None, *, uuid=None):
        key, value = self.use_id_or_uuid(id, uuid)
        sql = f"SELECT * FROM user_login WHERE {key}=%s"  # nosec
        async with self.cursor() as cursor:
            await cursor.execute(sql, (value,))
            row = await cursor.fetchone()
        return row

    async def close_login(self, id=None, *, uuid=None):
        key, value = self.use_id_or_uuid(id, uuid)
        sql = f"UPDATE user_login SET closed_ts=now_utc() WHERE {key}=%s RETURNING *"  # nosec
        async with self.cursor() as cursor:
            await cursor.execute(sql, (value,))
            row = await cursor.fetchone()
        return row

    # SESSION

    async def create_session(self, login_id):
        sql = "INSERT INTO user_session (login_id) VALUES (%s) RETURNING *"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (login_id,))
            row = await cursor.fetchone()
        return row

    async def get_session(self, id=None, *, uuid=None):
        key, value = self.use_id_or_uuid(id, uuid)
        sql = f"SELECT * FROM user_session WHERE {key}=%s"  # nosec
        async with self.cursor() as cursor:
            await cursor.execute(sql, (value,))
            row = await cursor.fetchone()
        return row

    async def get_session_info(self, id=None, *, uuid=None):
        key, value = self.use_id_or_uuid(id, uuid)
        sql = f"""
            SELECT 
                s.id session_id, s.uuid session_uuid, s.closed_ts session_closed_ts,
                l.id login_id, l.uuid login_uuid, l.closed_ts login_closed_ts,
                d.id device_id, d.uuid device_uuid, d.closed_ts device_closed_ts,
                l.user_id
            FROM user_session s
            JOIN user_login l ON l.id=s.login_id
            JOIN user_device d ON d.id=l.device_id
            WHERE s.{key}=%s
            """  # nosec
        async with self.cursor() as cursor:
            await cursor.execute(sql, (value,))
            row = await cursor.fetchone()
        return row

    async def close_session(self, id=None, *, uuid=None):
        key, value = self.use_id_or_uuid(id, uuid)
        async with self.cursor() as cursor:
            sql = f"UPDATE user_session SET closed_ts=now_utc() WHERE {key}=%s RETURNING *"  # nosec
            await cursor.execute(sql, (value,))
            row = await cursor.fetchone()
        return row

    # CLIENT

    async def create_client(self, session_id):
        async with self.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO user_client (session_id) VALUES (%s) RETURNING *",
                (session_id,),
            )
            row = await cursor.fetchone()
        return row

    async def get_client(self, id=None, *, uuid=None):
        key, value = self.use_id_or_uuid(id, uuid)
        async with self.cursor() as cursor:
            sql = f"SELECT * FROM user_client WHERE {key}=%s"  # nosec
            await cursor.execute(sql, (value,))
            row = await cursor.fetchone()
        return row

    async def get_client_info(self, id=None, *, uuid=None):
        key, value = self.use_id_or_uuid(id, uuid)
        sql = f"""
        select
            c.id client_id, c.closed_ts,
            c.session_id, s.login_id, l.user_id  
            from user_client c
            join user_session s on s.id = c.session_id 
            join user_login l on l.id = s.login_id
        where c.{key}=%s
        """  # nosec
        async with self.cursor() as cursor:
            await cursor.execute(sql, (value,))
            row = await cursor.fetchone()
        return row

    async def close_client(self, client_id):
        sql = "UPDATE user_client SET closed_ts=now_utc() WHERE id=%s RETURNING *"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (client_id,))
            row = await cursor.fetchone()
        return row

    # IMAGE

    async def create_image(self, owner_id, mime_type, image_data):
        if isinstance(image_data, bytes):
            image_data = base64.b64encode(image_data).decode()
        sql = (
            "INSERT INTO image (owner_id, mime_type, image_data) VALUES (%s, %s, %s) RETURNING id, owner_id, mime_type"
        )
        async with self.cursor() as cursor:
            await cursor.execute(sql, (owner_id, mime_type, image_data))
            row = await cursor.fetchone()
        return row

    async def get_image(self, id):
        sql = "SELECT * FROM image WHERE id=%s"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (id,))
            row = await cursor.fetchone()
        return row

    async def get_images_for_user(self, user_id):
        sql = "SELECT id, owner_id, mime_type FROM image WHERE owner_id=%s or owner_id IS NULL"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (user_id,))
            row = await cursor.fetchall()
        return row

    # LOBBY

    async def get_lobby_entry_tables(self):
        sql = "SELECT * FROM table_profile WHERE table_type='RG' and club_id IS NULL AND parent_id IS NULL AND closed_ts IS NULL"
        result = {}
        async with self.cursor() as cursor:
            await cursor.execute(sql)
            async for row in cursor:
                key = row.game_type, row.game_subtype
                if key in result:
                    continue
                result[key] = row
        return list(result.values())

    # CLUB

    async def create_club(self, *, user_id, name=None, description=None, image_id=None):
        club_sql = "INSERT INTO club_profile (name, description, image_id) VALUES (%s,%s,%s) RETURNING *"
        member_sql = "INSERT INTO user_account (club_id, user_id, user_role, approved_ts, approved_by) VALUES (%s,%s,%s,now_utc(),0)"
        async with self.cursor() as cursor:
            await cursor.execute(club_sql, (name, description, image_id))
            club = await cursor.fetchone()
            await cursor.execute(member_sql, (club.id, user_id, "O"))
        return club

    async def get_club(self, id):
        async with self.cursor() as cursor:
            await cursor.execute("SELECT * FROM club_profile WHERE id=%s", (id,))
            row = await cursor.fetchone()
        return row

    async def get_club_members(self, club_id):
        async with self.cursor() as cursor:
            await cursor.execute("SELECT * FROM user_account WHERE club_id=%s", (club_id,))
            rows = await cursor.fetchall()
        return rows

    async def update_club(self, id, **kwargs):
        params = ", ".join([f"{key}=%s" for key in kwargs])
        values = list(kwargs.values()) + [id]
        sql = f"UPDATE club_profile SET {params} WHERE id=%s RETURNING *"
        async with self.cursor() as cursor:
            await cursor.execute(sql, values)
            row = await cursor.fetchone()
        return row

    # USER ACCOUNT

    async def create_club_member(self, club_id, user_id, user_comment):
        sql = "INSERT INTO user_account (club_id, user_id, user_comment) VALUES (%s,%s,%s) RETURNING *"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (club_id, user_id, user_comment))
            row = await cursor.fetchone()
        return row

    async def get_club_member(self, member_id):
        async with self.cursor() as cursor:
            await cursor.execute("SELECT * FROM user_account WHERE id=%s", (member_id,))
            row = await cursor.fetchone()
        return row

    async def get_account_for_update(self, member_id):
        async with self.cursor() as cursor:
            await cursor.execute("SELECT * FROM user_account WHERE id=%s FOR UPDATE", (member_id,))
            row = await cursor.fetchone()
        return row

    async def create_account_txn(self, member_id, txntype, amount, sender_id):
        async with self.cursor() as cursor:
            sql = "UPDATE user_account SET balance=balance+(%s) WHERE id=%s RETURNING balance"
            await cursor.execute(sql, (amount, member_id))
            row = await cursor.fetchone()

            sql = "INSERT INTO user_account_txn (account_id, txn_type, txn_value, total_balance, sender_id) VALUES (%s, %s, %s, %s, %s) RETURNING *"
            await cursor.execute(sql, (member_id, txntype, amount, row.balance, sender_id))
            # txn = await cursor.fetchone()
        return row

    async def find_account(self, *, user_id, club_id):
        async with self.cursor() as cursor:
            await cursor.execute("SELECT * FROM user_account WHERE club_id=%s AND user_id=%s", (club_id, user_id))
            row = await cursor.fetchone()
        return row

    async def approve_club_member(self, member_id, approved_by, club_comment):
        sql = "UPDATE user_account SET approved_ts=now_utc(), approved_by=%s, club_comment=%s WHERE id=%s RETURNING *"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (approved_by, club_comment, member_id))
            row = await cursor.fetchone()
        return row

    async def close_club_member(self, member_id, closed_by, club_comment):
        sql = "UPDATE user_account SET closed_ts=now_utc(), closed_by=%s, club_comment=%s WHERE id=%s RETURNING *"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (closed_by, club_comment, member_id))
            row = await cursor.fetchone()
        return row

    async def get_clubs_for_user(self, user_id):
        sql = "SELECT c.*, m.user_role, m.approved_ts FROM user_account m JOIN club_profile c ON c.id=m.club_id WHERE c.id!=0 and m.user_id=%s and m.closed_ts IS NULL"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (user_id,))
            rows = await cursor.fetchall()
        return rows

    async def club_owner_update_user_account(self, account_id, data, row):
        if row == "nickname":
            sql = "UPDATE user_account SET nickname=%s WHERE id=%s"
        elif row == "club_comment":
            sql = "UPDATE user_account SET club_comment=%s WHERE id=%s"

        async with self.cursor() as cursor:
            await cursor.execute(sql, (data, account_id,))


    # TABLE

    async def create_table(self, *, club_id=0, table_type, table_name, table_seats, game_type, game_subtype,
                           props=None):
        props = json.dumps(props or {})
        sql = "INSERT INTO table_profile (club_id, table_type, table_name, table_seats, game_type, game_subtype, props) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING *"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (club_id, table_type, table_name, table_seats, game_type, game_subtype, props))
            row = await cursor.fetchone()
        return row

    async def get_table(self, table_id):
        sql = "SELECT * FROM table_profile WHERE id=%s"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (table_id,))
            row = await cursor.fetchone()
        return row

    async def get_open_tables(self):
        sql = "SELECT * FROM table_profile WHERE parent_id IS NULL and closed_ts IS NULL"
        async with self.cursor() as cursor:
            await cursor.execute(sql)
            rows = await cursor.fetchall()
        return rows

    async def get_club_tables(self, club_id):
        sql = "SELECT * FROM table_profile WHERE club_id=%s AND parent_id IS NULL and closed_ts IS NULL"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (club_id,))
            rows = await cursor.fetchall()
        return rows

    async def create_table_user(self, table_id, user_id):
        sql = "INSERT INTO table_user (table_id, user_id) VALUES (%s,%s) RETURNING *"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (table_id, user_id))
            row = await cursor.fetchone()
        return row

    async def lock_table_engine_id(self, table_id):
        sql = "UPDATE table_profile SET engine_id=pg_backend_pid(), engine_status=1 WHERE id=%s"
        await self.dbi.execute(sql, (table_id,))

    async def release_table_engine_id(self, table_id):
        sql = "UPDATE table_profile SET engine_id=NULL WHERE id=%s"
        await self.dbi.execute(sql, (table_id,))

    async def update_table_status(self, table_id, status):
        status = int(status)
        sql = "UPDATE table_profile SET engine_status=%s WHERE id=%s RETURNING *"
        async with self.cursor() as cursor:
            await cursor.execute(
                sql,
                (
                    status,
                    table_id,
                ),
            )
            row = await cursor.fetchone()
        return row

    async def close_table(self, table_id):
        # table closed
        sql = "UPDATE table_profile SET engine_status=9, closed_ts=now_utc() WHERE id=%s RETURNING *"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (table_id,))
            row = await cursor.fetchone()
        return row

    # TABLE SESSION

    async def find_table_session(self, table_id: int, account_id: int, for_update=True):
        sql = "SELECT s.*, extract(epoch from (now_utc()-closed_ts)) age_seconds FROM table_session s "
        sql += "WHERE table_id=%s and account_id=%s ORDER BY id DESC LIMIT 1 "
        if for_update:
            sql += "FOR UPDATE"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (table_id, account_id))
            row = await cursor.fetchone()
        return row

    async def register_table_session(self, table_id: int, account_id: int):
        row = await self.find_table_session(table_id, account_id, for_update=True)
        if not row or row.closed_ts:
            sql = "INSERT INTO table_session (table_id, account_id, opened_ts) VALUES(%s, %s, NULL) RETURNING *"
            async with self.cursor() as cursor:
                await cursor.execute(sql, (table_id, account_id))
                row = await cursor.fetchone()
        return row

    async def reuse_table_session(self, table_id: int, account_id: int):
        row = await self.find_table_session(table_id, account_id, for_update=True)
        if row:
            if not row.age_seconds:
                pass
            elif row.age_seconds < 3600:
                sql = "UPDATE table_session SET closed_ts=NULL WHERE id=%s RETURNING *"
                async with self.cursor() as cursor:
                    await cursor.execute(sql, (row.id,))
                    row = await cursor.fetchone()
            else:
                row = None
        if not row:
            sql = "INSERT INTO table_session (table_id, account_id, opened_ts) VALUES(%s, %s, now_utc()) RETURNING *"
            async with self.cursor() as cursor:
                await cursor.execute(sql, (table_id, account_id))
                row = await cursor.fetchone()
        return row

    async def open_table_session(self, table_session_id):
        sql = "UPDATE table_session SET opened_ts=now_utc(), closed_ts=NULL WHERE id=%s RETURNING *"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (table_session_id,))
            row = await cursor.fetchone()
        return row

    async def close_table_session(self, table_session_id):
        sql = "UPDATE table_session SET closed_ts=now_utc() WHERE id=%s RETURNING *"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (table_session_id,))
            row = await cursor.fetchone()
        return row

    async def get_table_result(self, table_id):
        sql = """
        SELECT tu.user_id, u.username, u.image_id, tu.last_game_id, gu.balance_begin, gu.balance_end, g.end_ts
        FROM poker_table_user tu
        JOIN user_profile u ON u.id=tu.user_id
        JOIN poker_game_user gu ON gu.user_id=tu.user_id and gu.game_id=tu.last_game_id
        JOIN poker_game g ON g.id=gu.game_id
        WHERE tu.table_id=%s
        """
        async with self.cursor() as cursor:
            await cursor.execute(sql, (table_id,))
            rows = cursor.fetchall()
        return rows

    # GAMES

    async def create_game(self, *, table_id: int, game_type, game_subtype, props, players):
        props = json.dumps(props or {})
        async with self.cursor() as cursor:
            sql = "INSERT INTO game_profile (table_id,game_type,game_subtype,props) VALUES (%s,%s,%s,%s) RETURNING *"
            await cursor.execute(sql, (table_id, game_type, game_subtype, props))
            game = await cursor.fetchone()
            if players:
                sql = "INSERT INTO game_player (game_id, user_id, balance_begin) VALUES (%s, %s, %s)"
                params_seq = [(game.id, u.id, u.balance) for u in players]
                await cursor.executemany(sql, params_seq)
        return game

    async def get_game_and_players(self, id: int):
        async with self.cursor() as cursor:
            await cursor.execute("SELECT * FROM game_profile WHERE id=%s", (id,))
            game = await cursor.fetchone()
            await cursor.execute("SELECT * FROM game_player WHERE game_id=%s", (id,))
            players = await cursor.fetchall()
        return game, players

    async def close_game(self, id: int, players):
        player_sql = "UPDATE game_player SET balance_end=%s WHERE game_id=%s AND user_id=%s"
        profile_sql = "UPDATE game_profile SET end_ts=now_utc() WHERE id=%s RETURNING *"
        async with self.cursor() as cursor:
            for u in players:
                await cursor.execute(player_sql, (u.balance, id, u.id))
            await cursor.execute(profile_sql, (id,))
            return await cursor.fetchone()

    async def all_players_games(self, user_id):
        sql = "SELECT game_id FROM game_player WHERE user_id=%s"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (user_id,))
            row = await cursor.fetchall()
        return row
    # EVENTS (TABLE_CMD)

    def json_dumps(self, obj):
        def encoder(x):
            if hasattr(x, "__int__"):
                return int(x)
            if hasattr(x, "__str__"):
                return str(x)
            type_name = x.__class__.__name__
            raise TypeError(f"Object of type {type_name} is not serializable")

        return json.dumps(obj, default=encoder)

    # EVENTS (TABLE_CMD)

    async def create_table_cmd(self, *, client_id, table_id, cmd_type, props):
        props = self.json_dumps(props or {})
        async with self.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO table_cmd (client_id, table_id, cmd_type, props) VALUES (%s,%s,%s,%s) RETURNING id, created_ts",
                (client_id, table_id, cmd_type, props),
            )
            return await cursor.fetchone()

    async def get_table_cmd(self, id):
        async with self.cursor() as cursor:
            await cursor.execute("SELECT * FROM table_cmd WHERE id=%s", (id,))
            row = await cursor.fetchone()
        return row

    async def set_table_cmd_processed(self, id):
        async with self.cursor() as cursor:
            await cursor.execute("UPDATE table_cmd SET processed_ts=now_utc() WHERE id=%s", (id,))

    # EVENTS (TABLE_MSG)

    async def create_table_msg(self, *, table_id, game_id, msg_type, props, cmd_id=None, client_id=None):
        props = self.json_dumps(props or {})
        async with self.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO table_msg (table_id, game_id, msg_type, props, cmd_id, client_id) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id, created_ts",
                (table_id, game_id, msg_type, props, cmd_id, client_id),
            )
            row = await cursor.fetchone()
        return row

    async def get_table_msg(self, id):
        async with self.cursor() as cursor:
            await cursor.execute("SELECT * FROM table_msg WHERE id=%s", (id,))
            row = await cursor.fetchone()
        return row

    # CLUB'S TXN
    async def check_request_to_replenishment(self, account_id):
        sql = "SELECT * FROM user_account_txn WHERE account_id=%s AND txn_type=%s ORDER BY id DESC LIMIT 1"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (account_id, "REPLENISHMENT"))
            row = await cursor.fetchone()
        return row

    async def txn_with_chip_on_club_balance(self, club_id, amount, mode, account_id, sender_id):
        if mode == 'CASHIN':
            sql = "UPDATE club_profile SET club_balance = club_balance + %s WHERE id=%s RETURNING club_balance"
        elif mode == 'REMOVE':
            sql = "UPDATE club_profile SET club_balance = club_balance - %s WHERE id=%s  RETURNING club_balance"
        async with self.cursor() as cursor:
            if mode == 'REMOVE':
                check_sql = "SELECT club_balance FROM club_profile WHERE id=%s"
                await cursor.execute(check_sql, (club_id,))
                club_balance = await cursor.fetchone()

                if (club_balance.club_balance - amount) < 0.0:
                    reset_balance_sql = "UPDATE club_profile SET club_balance = 0 WHERE id=%s"
                    await cursor.execute(reset_balance_sql, (club_id,))
                    sql = "INSERT INTO user_account_txn (account_id, txn_type, txn_value, total_balance, sender_id) VALUES (%s, %s, %s, %s, %s) RETURNING *"
                    await cursor.execute(sql, (account_id, f"CLUB_{mode}", amount, 0, sender_id))
                    return

            await cursor.execute(sql, (amount, club_id))
            row = await cursor.fetchone()
            sql = "INSERT INTO user_account_txn (account_id, txn_type, txn_value, total_balance, sender_id) VALUES (%s, %s, %s, %s, %s) RETURNING *"
            await cursor.execute(sql, (account_id, f"CLUB_{mode}", amount, row.club_balance, sender_id))

    async def send_request_for_replenishment_of_chips(self, account_id, amount, balance):
        sql = "INSERT INTO public.user_account_txn (account_id, txn_type, txn_value, props) VALUES (%s, %s, %s, %s::jsonb)"
        txn_type = "REPLENISHMENT"
        props = {"balance": balance, "status": "consider"}
        props_json = json.dumps(props)  # Преобразование словаря в JSON-строку
        async with self.cursor() as cursor:
            await cursor.execute(sql, (account_id, txn_type, amount, props_json))
        return

    async def get_user_balance_in_club(self, club_id, user_id):
        async with self.cursor() as cursor:
            await cursor.execute("SELECT balance FROM user_account WHERE club_id = %s AND user_id = %s",
                                 (club_id, user_id))
            row = await cursor.fetchone()
            if row.balance < 0:
                return 0
        return row.balance

    async def get_balance_shared_in_club(self, club_id, user_id):
        async with self.cursor() as cursor:
            await cursor.execute("SELECT user_role FROM user_account WHERE club_id = %s AND user_id = %s",
                                 (club_id, user_id))
            role = await cursor.fetchone()
            if role.user_role == "A" or role.user_role == "SA" or role.user_role == "O":
                await cursor.execute("SELECT balance_shared FROM user_account WHERE club_id = %s AND user_id = %s",
                                     (club_id, user_id))
                row = await cursor.fetchone()
                return row.balance_shared
            else:
                return None

    async def get_service_balance_in_club(self, club_id, user_id):
        async with self.cursor() as cursor:
            await cursor.execute("SELECT user_role FROM user_account WHERE club_id = %s AND user_id = %s",
                                 (club_id, user_id))
            role = await cursor.fetchone()
            if role.user_role == "O":
                await cursor.execute("SELECT service_balance FROM club_profile WHERE id = %s ", (club_id,))
                row = await cursor.fetchone()
                return row.service_balance
            else:
                return None

    async def giving_chips_to_the_user(self, amount, user_account_id, balance, sender_id):
        if balance == "balance":
            sql = "UPDATE user_account SET balance = balance + %s WHERE id = %s RETURNING balance"
        elif balance == "balance_shared":
            sql = "UPDATE user_account SET balance_shared = balance_shared + %s WHERE id = %s RETURNING balance"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (amount, user_account_id))
            row = await cursor.fetchone()

            sql = "INSERT INTO user_account_txn (account_id, txn_type, txn_value, total_balance, sender_id) VALUES (%s, %s, %s, %s, %s) RETURNING *"
            await cursor.execute(sql, (user_account_id, "CASHIN", amount, row.balance, sender_id))

    async def delete_chips_from_the_agent_balance(self, amount, account_id, sender_id):
        get_balance_shared_sql = "SELECT balance_shared FROM user_account WHERE id = %s"
        sql = "UPDATE user_account SET balance_shared = balance_shared - %s WHERE id = %s RETURNING balance_shared"
        async with self.cursor() as cursor:
            await cursor.execute(get_balance_shared_sql, (account_id,))
            balance_shared = await cursor.fetchone()

            if (balance_shared.balance_shared - amount) < 0:
                sql = "UPDATE user_account SET balance_shared = 0 WHERE id = %s"
                await cursor.execute(sql, (account_id,))
                return

            await cursor.execute(sql, (amount, account_id,))
            row = await cursor.fetchone()
            sql = "INSERT INTO user_account_txn (account_id, txn_type, txn_value, total_balance, sender_id) VALUES (%s, %s, %s, %s, %s) RETURNING *"
            await cursor.execute(sql, (account_id, "REMOVE", amount, row.balance_shared, sender_id))
            return

    async def delete_chips_from_the_account_balance(self, amount, account_id, sender_id):
        get_balance_shared_sql = "SELECT balance FROM user_account WHERE id = %s"
        sql = "UPDATE user_account SET balance = balance - %s WHERE id = %s RETURNING balance"

        async with self.cursor() as cursor:
            await cursor.execute(get_balance_shared_sql, (account_id,))
            balance = await cursor.fetchone()
            print(type(balance.balance), type(amount))
            if (balance.balance - amount) <= 0:
                sql = "UPDATE user_account SET balance = 0 WHERE id = %s"
                await cursor.execute(sql, (account_id,))
                return
            await cursor.execute(sql, (amount, account_id,))
            row = await cursor.fetchone()
            sql = "INSERT INTO user_account_txn (account_id, txn_type, txn_value, total_balance, sender_id) VALUES (%s, %s, %s, %s, %s) RETURNING *"
            await cursor.execute(sql, (account_id, "REMOVE", amount, row.balance, sender_id))
        return

    async def leave_from_club(self, account_id):
        closed_time = datetime.datetime.utcnow()
        sql = "UPDATE user_account SET closed_ts=%s, closed_by=%s WHERE id=%s"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (closed_time, account_id, account_id,))

    async def return_member_in_club(self, account_id):
        closed_time = datetime.datetime.utcnow()
        sql = "UPDATE user_account SET created_ts=%s, closed_ts=%s, closed_by=%s WHERE id=%s"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (closed_time, None, None, account_id,))

    async def get_user_history_trx_in_club(self, user_id, club_id):
        sql_history = "SELECT * FROM user_account_txn WHERE account_id=%s"
        sql_users_accounts = "SELECT id FROM user_account WHERE user_id=%s AND club_id=%s"
        result_list = []
        async with self.cursor() as cursor:
            await cursor.execute(sql_users_accounts, (user_id, club_id))
            rows_ids = await cursor.fetchall()
            for a_id in rows_ids:
                await cursor.execute(sql_history, (a_id.id,))
                row = await cursor.fetchall()
                result_list.append(row)
        return row

    async def get_user_requests_to_replenishment(self, account_id):
        sql = "SELECT txn_value FROM user_account_txn WHERE account_id = %s AND props @> %s::jsonb"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (account_id, json.dumps({"status": "consider"})))
            row = await cursor.fetchone()
        return row
        # ACCOUNT STATISTICS

    async def statistics_of_games_played(self, table_id, date):
        date_now = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        tomorrow = date_now + datetime.timedelta(days=1)
        sql = "SELECT * FROM public.game_profile WHERE table_id = %s AND end_ts >= %s AND end_ts < %s"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (table_id, date_now, tomorrow,))
            row = await cursor.fetchall()

        return row

    async def get_statistics_about_winning(self, account_id, date):
        sql = "SELECT * FROM user_account_txn WHERE account_id=%s AND created_ts >= %s AND created_ts < %s"
        date_now = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        tomorrow = date_now + datetime.timedelta(days=1)
        async with self.cursor() as cursor:
            await cursor.execute(sql, (account_id, date_now, tomorrow))
            row = await cursor.fetchall()

        return row

    async def check_game_by_date(self, game_id, date):
        date_now = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        sql = "SELECT * FROM game_profile WHERE id=%s AND CAST(end_ts AS DATE) = %s"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (game_id, date_now))
            row = await cursor.fetchone()
        return row

    async def get_balance_begin_and_end_from_game(self, game_id, user_id):
        sql = "SELECT balance_begin, balance_end, game_id FROM game_player WHERE game_id=%s AND user_id=%s"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (game_id, user_id))
            row = await cursor.fetchone()
        return row
