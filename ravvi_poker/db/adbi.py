import logging
import os
import json
import psycopg
import psycopg_pool
from psycopg.rows import namedtuple_row, dict_row
from psycopg.connection import Notify

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

    async def create_user_client(self, session_id):
        async with self.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO user_client (session_id) VALUES (%s) RETURNING id, opened_ts",
                (session_id,),
            )
            row = await cursor.fetchone()
            return row

    async def close_user_client(self, client_id):
        async with self.cursor() as cursor:
            await cursor.execute(
                "UPDATE user_client SET closed_ts=now_utc() WHERE id=%s RETURNING closed_ts",
                (client_id,),
            )
            row = await cursor.fetchone()
            return row

    # TABLES

    async def create_table(self, club_id, **kwargs):
        # split base and extra props
        row = {}
        columns = ["table_type", "table_name", "table_seats", "game_type", "game_subtype"]
        for k in columns:
            v = kwargs.pop(k, None)
            row[k] = v
        row.update(game_settings=json.dumps(kwargs))
        async with self.cursor() as cursor:
            fields = ", ".join(["club_id"] + list(row.keys()))
            values = [club_id] + list(row.values())
            values_pattern = ", ".join(["%s"] * len(values))
            sql = f"INSERT INTO poker_table ({fields}) VALUES ({values_pattern}) RETURNING *"
            await cursor.execute(sql, values)
            row = await cursor.fetchone()
            if row is not None:
                props = row.pop("game_settings", {})
                row.update(props)
        return row
    
#    def set_table_opened(self, table_id):
#        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
#            cursor.execute("UPDATE poker_table SET opened_ts=NOW() WHERE id=%s RETURNING opened_ts",(table_id,))
#            row = cursor.fetchone()
#            return row.opened_ts if row else None

    async def close_table(self, table_id):
        async with self.cursor() as cursor:
            await cursor.execute("UPDATE poker_table SET closed_ts=now_utc() WHERE id=%s RETURNING closed_ts",(table_id,))
            row = await cursor.fetchone()
            return row.closed_ts if row else None
    
    async def create_table_user(self, table_id, user_id):
        async with self.cursor() as cursor:
            sql = f"INSERT INTO poker_table_user (table_id, user_id) VALUES (%s,%s)"
            await cursor.execute(sql, (table_id, user_id))

#    def table_user_game(self, table_id, user_id, last_game_id):
#        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
#            sql = f"UPDATE poker_table_user SET last_game_id=%s WHERE table_id=%s AND user_id=%s"
#            cursor.execute(sql, (last_game_id, table_id, user_id))

    # EVENTS

    async def emit_event(self, event):
        return await self.save_event(**event)

    async def save_event(self, *, type, table_id, game_id=None, user_id=None, client_id=None, **kwargs):
        logger.debug("save_event: %s %s/%s %s/%s %s", type, table_id, game_id, user_id, client_id, kwargs)
        props = json.dumps(kwargs) if kwargs else None
        async with self.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO poker_event (table_id, client_id, game_id, user_id, event_type, event_props) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id, event_ts",
                (table_id, client_id, game_id, user_id, type, props),
            )
            row = await cursor.fetchone()
            return row
    
    async def get_event(self, event_id):
        async with self.cursor() as cursor:
            await cursor.execute('SELECT * FROM poker_event WHERE id=%s', (event_id,))
            return await cursor.fetchone()

    async def get_open_tables(self):
        async with self.cursor() as cursor:
            await cursor.execute("SELECT * FROM poker_table WHERE parent_id IS NULL and closed_ts IS NULL")
            rows = await cursor.fetchall()
        return rows
    
    # GAMES
    async def create_game(self, *, table_id, users, game_type, game_subtype, game_props):
        game = None
        async with self.cursor() as cursor:
            await cursor.execute("INSERT INTO poker_game (table_id,game_type,game_subtype,begin_ts) VALUES (%s,%s,%s,now_utc()) RETURNING *",
                           (table_id, game_type, game_subtype))
            game = await cursor.fetchone()
            params_seq = [(game.id, u.id, u.balance) for u in users]
            await cursor.executemany("INSERT INTO poker_game_user (game_id, user_id, balance_begin) VALUES (%s, %s, %s)", params_seq)
        return game

    async def close_game(self, game_id, users):
        async with self.cursor() as cursor:
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
