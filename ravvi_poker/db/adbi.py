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

    ForeignKeyViolation = psycopg.errors.ForeignKeyViolation

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
        logger.debug("pool: ready")

    @classmethod
    async def pool_close(cls):
        await cls.pool.close()
        cls.pool = None
        logger.debug("pool: closed")

    def __init__(self) -> None:
        self.dbi = None

    # CONTEXT

    async def __aenter__(self):
        self.dbi = await self.pool.getconn()
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        if exc_type is None:
            await self.dbi.commit()
        else:
            await self.dbi.rollback()
        await self.pool.putconn(self.dbi)
        self.dbi = None

    def cursor(self, *args, row_factory=namedtuple_row, **kwargs):
        return self.dbi.cursor(*args, row_factory=row_factory, **kwargs)
    
    def use_id_or_uuid(self, id, uuid):
        if id is not None:
            key, value = 'id', id
        elif uuid is not None:
            key, value = 'uuid', uuid
        else:
            raise ValueError('login: id or uuid required')
        return key, value

    async def listen(self, channel):
        await self.dbi.execute(f'LISTEN {channel}')

    # DEVICE 

    async def create_device(self, props=None):
        props = json.dumps(props) if props else None
        async with self.cursor() as cursor:
            args = "INSERT INTO user_device (props) VALUES (%s) RETURNING *", (props,)
            await cursor.execute(*args)
            row = await cursor.fetchone()
        return row
        
    async def get_device(self, id=None, *, uuid=None):
        key, value = self.use_id_or_uuid(id, uuid)
        async with self.cursor() as cursor:
            await cursor.execute(f"SELECT * FROM user_device WHERE {key}=%s", (value,))
            row = await cursor.fetchone()
        return row
        
    # USER

    async def create_user(self):
        async with self.cursor() as cursor:
            await cursor.execute("INSERT INTO user_profile (username) VALUES (NULL) RETURNING *")
            row = await cursor.fetchone()
        return row

    async def get_user(self, id=None, *, uuid=None):
        key, value = self.use_id_or_uuid(id, uuid)
        async with self.cursor() as cursor:
            await cursor.execute(f"SELECT * FROM user_profile WHERE {key}=%s", (value,))
            row = await cursor.fetchone()
        return row

    async def close_user(self, id=None, *, uuid=None):
        key, value = self.use_id_or_uuid(id, uuid)
        async with self.cursor() as cursor:
            await cursor.execute(f"UPDATE user_profile SET closed_ts=now_utc() WHERE {key}=%s RETURNING *", (value,))
            row = await cursor.fetchone()
        return row
    
    # LOGIN

    async def create_login(self, device_id, user_id):
        async with self.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO user_login (device_id, user_id) VALUES (%s, %s) RETURNING *",
                (device_id, user_id),
            )
            row = await cursor.fetchone()
        return row
        
    async def get_login(self, id=None, *, uuid=None):
        key, value = self.use_id_or_uuid(id, uuid)
        async with self.cursor() as cursor:
            await cursor.execute(f"SELECT * FROM user_login WHERE {key}=%s", (value,))
            row = await cursor.fetchone()
        return row
        
    async def close_login(self, id=None, *, uuid=None):
        key, value = self.use_id_or_uuid(id, uuid)
        async with self.cursor() as cursor:
            await cursor.execute(f"UPDATE user_login SET closed_ts=now_utc() WHERE {key}=%s RETURNING *", (value,))
            row = await cursor.fetchone()
        return row
                    
    # SESSION

    async def create_session(self, login_id):
        async with self.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO user_session (login_id) VALUES (%s) RETURNING *",
                (login_id,),
            )
            row = await cursor.fetchone()
        return row

    async def get_session(self, id=None, *, uuid=None):
        key, value = self.use_id_or_uuid(id, uuid)
        async with self.cursor() as cursor:
            await cursor.execute(f"SELECT * FROM user_session WHERE {key}=%s", (value,))
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
            """
        async with self.cursor() as cursor:
            await cursor.execute(sql, (value,))
            row = await cursor.fetchone()
        return row

    async def close_session(self, id=None, *, uuid=None):
        key, value = self.use_id_or_uuid(id, uuid)
        async with self.cursor() as cursor:
            await cursor.execute(
                f"UPDATE user_session SET closed_ts=now_utc() WHERE {key}=%s RETURNING *",
                (value,),
            )
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
            await cursor.execute(f"SELECT * FROM user_client WHERE {key}=%s", (value,))
            row = await cursor.fetchone()
        return row
    
    async def get_client_info(self, id=None, *, uuid=None):
        key, value = self.use_id_or_uuid(id, uuid)
        async with self.cursor() as cursor:
            sql = f"""
            select
                c.id client_id, c.closed_ts,
                c.session_id, s.login_id, l.user_id  
                from user_client c
                join user_session s on s.id = c.session_id 
                join user_login l on l.id = s.login_id
            where c.{key}=%s
            """
            await cursor.execute(sql, (value,))
            row = await cursor.fetchone()
        return row

    async def close_client(self, client_id):
        async with self.cursor() as cursor:
            await cursor.execute(
                "UPDATE user_client SET closed_ts=now_utc() WHERE id=%s RETURNING *",
                (client_id,),
            )
            row = await cursor.fetchone()
        return row

    # TABLE

    async def create_table(self, *, club_id=None, table_type, table_name, table_seats, game_type, game_subtype, props=None):
        props = json.dumps(props or {})
        async with self.cursor() as cursor:
            sql = "INSERT INTO table_profile (club_id, table_type, table_name, table_seats, game_type, game_subtype, props) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING *"
            await cursor.execute(sql, (club_id, table_type, table_name, table_seats, game_type, game_subtype, props))
            row = await cursor.fetchone()
        return row
    
    async def get_table(self, table_id):
        async with self.cursor() as cursor:
            await cursor.execute("SELECT * FROM table_profile WHERE id=%s", (table_id,))
            row = await cursor.fetchone()
        return row    

    async def get_open_tables(self):
        async with self.cursor() as cursor:
            await cursor.execute("SELECT * FROM table_profile WHERE parent_id IS NULL and closed_ts IS NULL")
            rows = await cursor.fetchall()
        return rows

    async def create_table_user(self, table_id, user_id):
        async with self.cursor() as cursor:
            sql = f"INSERT INTO table_user (table_id, user_id) VALUES (%s,%s) RETURNING *"
            await cursor.execute(sql, (table_id, user_id))
            row = await cursor.fetchone()
        return row

    async def close_table(self, table_id):
        async with self.cursor() as cursor:
            await cursor.execute("UPDATE table_profile SET closed_ts=now_utc() WHERE id=%s RETURNING *",(table_id,))
            row = await cursor.fetchone()
        return row
        
    # EVENTS

    async def emit_event(self, event):
        return await self.save_event(**event)

    async def save_event(self, *, type, table_id, game_id=None, user_id=None, client_id=None, **kwargs):
        logger.debug("save_event: %s %s/%s %s/%s %s", type, table_id, game_id, user_id, client_id, kwargs)
        props = json.dumps(kwargs) if kwargs else None
        async with self.cursor() as cursor:
            await cursor.execute(
                "INSERT INTO \"event\" (table_id, client_id, game_id, type, props) VALUES (%s, %s, %s, %s, %s) RETURNING id, created_ts",
                (table_id, client_id, game_id, user_id, type, props),
            )
            return await cursor.fetchone()
    
    async def get_event(self, event_id):
        async with self.cursor() as cursor:
            await cursor.execute('SELECT * FROM \"event\" WHERE id=%s', (event_id,))
            return await cursor.fetchone()
    
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


