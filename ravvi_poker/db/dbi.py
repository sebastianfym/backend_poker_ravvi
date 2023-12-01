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
    DB_USER = os.getenv("RAVVI_POKER_DB_USER", "postgres")
    DB_PASSWORD = os.getenv("RAVVI_POKER_DB_PASSWORD", "password")
    DB_NAME = os.getenv("RAVVI_POKER_DB_NAME", "develop")
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
            connect_timeout = cls.CONNECT_TIMEOUT,
            application_name=cls.APPLICATION_NAME,
        )
        return conninfo

    @classmethod
    async def pool_open(cls):
#        cls.pool_ref += 1
#        if cls.pool_ref == 1:
        cls.pool = psycopg_pool.AsyncConnectionPool(conninfo=cls.conninfo(), open=False)
        await cls.pool.open()
        logger.debug("pool: ready")

    @classmethod
    async def pool_close(cls):
#        cls.pool_ref -= 1
#        if cls.pool_ref==0:
        await cls.pool.close()
        cls.pool = None
        logger.debug("pool: closed")

    def __init__(self) -> None:
        self.dbi_pool = None
        self.dbi = None

    # CONTEXT

    async def __aenter__(self):
        if self.pool:
            self.dbi_pool = self.pool
            self.dbi = await self.dbi_pool.getconn(timeout=self.CONNECT_TIMEOUT)
        else:
            self.dbi = await psycopg.AsyncConnection.connect(self.conninfo())
        #logger.info('connection open')
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        if exc_type is None:
            await self.dbi.commit()
        else:
            await self.dbi.rollback()
        if self.dbi_pool:
            await self.dbi_pool.putconn(self.dbi)
            self.dbi_pool = None
        else:
            await self.dbi.close()
        #logger.info('connection closed')
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

    async def unlisten(self, channel):
        await self.dbi.execute(f'UNLISTEN {channel}')

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
        sql = f"SELECT * FROM user_device WHERE {key}=%s" # nosec
        async with self.cursor() as cursor:
            await cursor.execute(sql, (value,))
            row = await cursor.fetchone()
        return row
        
    # USER

    async def create_user(self):
        sql = "INSERT INTO user_profile (username) VALUES (NULL) RETURNING *"
        async with self.cursor() as cursor:
            await cursor.execute(sql)
            row = await cursor.fetchone()
        return row

    async def get_user(self, id=None, *, uuid=None):
        key, value = self.use_id_or_uuid(id, uuid)
        sql = f"SELECT * FROM user_profile WHERE {key}=%s" # nosec
        async with self.cursor() as cursor:
            await cursor.execute(sql, (value,))
            row = await cursor.fetchone()
        return row

    async def update_user(self, id, **kwargs):
        params = ", ".join([f"{key}=%s" for key in kwargs])
        values = list(kwargs.values()) + [id]
        sql = f"UPDATE user_profile SET {params} WHERE id=%s RETURNING *"
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
        sql = f"UPDATE user_profile SET closed_ts=now_utc() WHERE {key}=%s RETURNING *" # nosec
        async with self.cursor() as cursor:
            await cursor.execute(sql, (value,))
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
        sql = f"SELECT * FROM user_login WHERE {key}=%s" # nosec
        async with self.cursor() as cursor:
            await cursor.execute(sql, (value,))
            row = await cursor.fetchone()
        return row
        
    async def close_login(self, id=None, *, uuid=None):
        key, value = self.use_id_or_uuid(id, uuid)
        sql = f"UPDATE user_login SET closed_ts=now_utc() WHERE {key}=%s RETURNING *" # nosec
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
        sql = f"SELECT * FROM user_session WHERE {key}=%s" # nosec
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
            """ # nosec
        async with self.cursor() as cursor:
            await cursor.execute(sql, (value,))
            row = await cursor.fetchone()
        return row

    async def close_session(self, id=None, *, uuid=None):
        key, value = self.use_id_or_uuid(id, uuid)
        async with self.cursor() as cursor:
            sql = f"UPDATE user_session SET closed_ts=now_utc() WHERE {key}=%s RETURNING *" # nosec
            await cursor.execute( sql, (value,))
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
            sql = f"SELECT * FROM user_client WHERE {key}=%s" # nosec
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
        """ # nosec
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
        sql = "INSERT INTO image (owner_id, mime_type, image_data) VALUES (%s, %s, %s) RETURNING id, owner_id, mime_type"
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
        club_sql = "INSERT INTO club (founder_id, name, description, image_id) VALUES (%s,%s,%s,%s) RETURNING *"
        member_sql = "INSERT INTO club_member (club_id, user_id, user_role, approved_ts, approved_by) VALUES (%s,%s,%s,now_utc(),0)"
        async with self.cursor() as cursor:
            await cursor.execute(club_sql,(user_id, name, description, image_id))
            club = await cursor.fetchone()
            await cursor.execute(member_sql,(club.id, user_id,'OWNER'))
        return club

    async def get_club(self, id):
        async with self.cursor() as cursor:
            await cursor.execute("SELECT * FROM club WHERE id=%s",(id,))
            row = await cursor.fetchone()
        return row

    async def get_club_members(self, club_id):
        async with self.cursor() as cursor:
            await cursor.execute("SELECT * FROM club_member WHERE club_id=%s", (club_id,))
            rows = await cursor.fetchall()
        return rows

    async def update_club(self, id, **kwargs):
        params = ", ".join([f"{key}=%s" for key in kwargs])
        values = list(kwargs.values()) + [id]
        sql = f"UPDATE club SET {params} WHERE id=%s RETURNING *"
        async with self.cursor() as cursor:
            await cursor.execute(sql, values)
            row = await cursor.fetchone()
        return row

    async def create_club_member(self, club_id, user_id, user_comment):
        sql = "INSERT INTO club_member (club_id, user_id, user_comment, user_role, approved_ts, approved_by) VALUES (%s,%s,%s,%s,NULL,NULL) RETURNING *"
        async with self.cursor() as cursor:
            await cursor.execute(sql,(club_id, user_id, user_comment,'PLAYER'))
            row = await cursor.fetchone()
        return row

    async def get_club_member(self, member_id):
        async with self.cursor() as cursor:
            await cursor.execute("SELECT * FROM club_member WHERE id=%s",(member_id,))
            row = await cursor.fetchone()
        return row

    async def find_club_member(self, club_id, user_id):
        async with self.cursor() as cursor:
            await cursor.execute("SELECT * FROM club_member WHERE club_id=%s AND user_id=%s",(club_id, user_id))
            row = await cursor.fetchone()
        return row

    async def approve_club_member(self, member_id, approved_by, club_comment):
        sql = "UPDATE club_member SET approved_ts=now_utc(), approved_by=%s, club_comment=%s WHERE id=%s RETURNING *"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (approved_by, club_comment, member_id))
            row = await cursor.fetchone()
        return row

    async def close_club_member(self, member_id, closed_by, club_comment):
        sql = "UPDATE club_member SET closed_ts=now_utc(), closed_by=%s, club_comment=%s WHERE id=%s RETURNING *"
        async with self.cursor() as cursor:
            await cursor.execute(sql,(closed_by, club_comment, member_id))
            row = await cursor.fetchone()
        return row

    async def get_clubs_for_user(self, user_id):
        sql = "SELECT c.*, m.user_role, m.approved_ts FROM club_member m JOIN club c ON c.id=m.club_id WHERE m.user_id=%s and m.closed_ts IS NULL"
        async with self.cursor() as cursor:
            await cursor.execute(sql,(user_id,))
            rows = await cursor.fetchall()
        return rows

    # TABLE

    async def create_table(self, *, club_id=None, table_type, table_name, table_seats, game_type, game_subtype, props=None):
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

    async def create_table_user(self, table_id, user_id):
        sql = "INSERT INTO table_user (table_id, user_id) VALUES (%s,%s) RETURNING *"
        async with self.cursor() as cursor:
            await cursor.execute(sql, (table_id, user_id))
            row = await cursor.fetchone()
        return row

    async def lock_table_engine_id(self, table_id):
        sql = "UPDATE table_profile SET engine_id=pg_backend_pid(), engine_status=1 WHERE id=%s"
        await self.dbi.execute(sql,(table_id,))

    async def release_table_engine_id(self, table_id):
        sql = "UPDATE table_profile SET engine_id=NULL WHERE id=%s"
        await self.dbi.execute(sql,(table_id,))

    async def update_table_status(self, table_id, status):
        status = int(status)
        sql = "UPDATE table_profile SET engine_status=%s WHERE id=%s RETURNING *"
        async with self.cursor() as cursor:
            await cursor.execute(sql,(status,table_id,))
            row = await cursor.fetchone()
        return row

    async def close_table(self, table_id):
        # table closed
        sql = "UPDATE table_profile SET engine_status=9, closed_ts=now_utc() WHERE id=%s RETURNING *"
        async with self.cursor() as cursor:
            await cursor.execute(sql,(table_id,))
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
            await cursor.execute(sql,(table_id,))
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

    # EVENTS (TABLE_CMD)

    def json_dumps(self, obj):
        def encoder(x):
            if hasattr(x, '__int__'):
                return int(x)
            if hasattr(x, '__str__'):
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
            return await cursor.fetchone()

    async def get_table_msg(self, id):
        async with self.cursor() as cursor:
            await cursor.execute("SELECT * FROM table_msg WHERE id=%s", (id,))
            row = await cursor.fetchone()
        return row
    