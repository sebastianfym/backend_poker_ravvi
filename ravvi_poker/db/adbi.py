import logging
import os
import json
import psycopg
import psycopg_pool
from psycopg.rows import namedtuple_row, dict_row

logger = logging.getLogger(__name__)


class DBI:
    DB_HOST = os.getenv("RAVVI_POKER_DB_HOST", "localhost")
    DB_PORT = int(os.getenv("RAVVI_POKER_DB_PORT", "15432"))
    DB_USER = os.getenv("RAVVI_POKER_DB_USER", "postgres")
    DB_PASSWORD = os.getenv("RAVVI_POKER_DB_PASSWORD", "password")
    DB_NAME = os.getenv("RAVVI_POKER_DB_NAME", "develop")

    pool = None

    @classmethod
    def conninfo(cls, db_name: str | None = None):
        conninfo = psycopg.conninfo.make_conninfo(
            host=cls.DB_HOST,
            port=cls.DB_PORT,
            dbname=db_name or cls.DB_NAME,
            user=cls.DB_USER,
            password=cls.DB_PASSWORD,
        )
        return conninfo

    @classmethod
    async def pool_open(cls):
        cls.pool = psycopg_pool.AsyncConnectionPool(conninfo=cls.conninfo(), open=False)
        await cls.pool.open()

    @classmethod
    async def pool_close(cls):
        await cls.pool.close()

    def __init__(self) -> None:
        self.dbi = None

    async def __aenter__(self):
        self.dbi = await self.pool.getconn()
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        if not self.dbi:
            return
        if exc_type is None:
            await self.dbi.commit()
        else:
            await self.dbi.rollback()
        await self.pool.putconn(self.dbi)
        self.dbi = None

    def txn(self):
        return DBI_Txn(self.dbi)

    async def execute(self, query, **kwargs):
        return await self.dbi.execute(query, params=kwargs)

    def cursor(self, *args, row_factory=namedtuple_row, **kwargs):
        return self.dbi.cursor(*args, row_factory=row_factory, **kwargs)

    async def get_session_info(self, *, uuid):
        sql = """
            SELECT 
                s.id session_id, s.uuid session_uuid, 
                l.id login_id, l.uuid login_uuid,
                d.id device_id, d.uuid device_uuid,
                l.user_id
            FROM user_session s
            JOIN user_login l ON l.id=s.login_id
            JOIN user_device d ON d.id=l.device_id
            WHERE s.uuid=%s
            """
        async with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            await cursor.execute(sql, (uuid,))
            row = await cursor.fetchone()
            return row

    async def ws_client_create(self, session_id):
        async with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            await cursor.execute(
                "INSERT INTO user_ws_client (session_id) VALUES (%s) RETURNING id, created_ts",
                (session_id,),
            )
            row = await cursor.fetchone()
            return row

    async def ws_client_close(self, client_id):
        async with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            await cursor.execute(
                "UPDATE user_ws_client SET closed_ts=now_utc() WHERE id=%s RETURNING closed_ts",
                (client_id,),
            )
            row = await cursor.fetchone()
            return row

    async def save_event(self, *, type, table_id, game_id=None, user_id=None, client_id=None, **kwargs):
        props = json.dumps(kwargs) if kwargs else None
        async with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            await cursor.execute(
                "INSERT INTO poker_event (table_id, client_id, game_id, user_id, event_type, event_props) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id, event_ts",
                (table_id, client_id, game_id, user_id, type, props),
            )
            row = await cursor.fetchone()
            return row

    async def get_open_tables(self):
        async with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            await cursor.execute("SELECT * FROM poker_table WHERE parent_id IS NULL and closed_ts IS NULL")
            rows = await cursor.fetchall()
        return rows
    
    # GAMES
    async def game_begin(self, *, table_id, users, game_type, game_subtype, game_props):
        game = None
        async with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            await cursor.execute("INSERT INTO poker_game (table_id,game_type,game_subtype,begin_ts) VALUES (%s,%s,%s,now_utc()) RETURNING *",
                           (table_id, game_type, game_subtype))
            game = await cursor.fetchone()
            params_seq = [(game.id, u.id, u.balance) for u in users]
            await cursor.executemany("INSERT INTO poker_game_user (game_id, user_id, balance_begin) VALUES (%s, %s, %s)", params_seq)
        return game

    async def game_end(self, game_id, users):
        async with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            for u in users:
                await cursor.execute("UPDATE poker_game_user SET balance_end=%s WHERE game_id=%s AND user_id=%s",
                               (u.balance, game_id, u.id))
            await cursor.execute("UPDATE poker_game SET end_ts=now_utc() WHERE id=%s RETURNING *",(game_id,))
            return await cursor.fetchone()


class DBI_Txn:
    def __init__(self, dbi=None) -> None:
        self.dbi = dbi

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        if not self.dbi:
            return
        if exc_type is None:
            await self.dbi.commit()
        else:
            await self.dbi.rollback()
        self.dbi = None
