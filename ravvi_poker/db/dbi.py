import logging
import os
import json
import psycopg
from psycopg.rows import namedtuple_row

logger = logging.getLogger(__name__)

class DBI:
    DB_HOST = os.getenv("RAVVI_POKER_DB_HOST", "localhost")
    DB_PORT = int(os.getenv("RAVVI_POKER_DB_PORT", "15432"))
    DB_USER = os.getenv("RAVVI_POKER_DB_USER", "postgres")
    DB_PASSWORD = os.getenv("RAVVI_POKER_DB_PASSWORD", "password")
    DB_NAME = os.getenv("RAVVI_POKER_DB_NAME", "develop")

    @classmethod
    def create_database(cls, db_name):
        conninfo = psycopg.conninfo.make_conninfo(
            host=cls.DB_HOST,
            port=cls.DB_PORT,
            user=cls.DB_USER,
            password=cls.DB_PASSWORD,
            dbname="postgres",
        )
        with psycopg.connect(conninfo, autocommit=True) as dbi:
            with dbi.cursor() as cur:
                dbi.execute(f"CREATE DATABASE {db_name} TEMPLATE template0")

    @classmethod
    def drop_database(cls, db_name):
        conninfo = psycopg.conninfo.make_conninfo(
            host=cls.DB_HOST,
            port=cls.DB_PORT,
            user=cls.DB_USER,
            password=cls.DB_PASSWORD,
            dbname="postgres",
        )
        with psycopg.connect(conninfo, autocommit=True) as dbi:
            with dbi.cursor() as cur:
                cur.execute(f"DROP DATABASE IF EXISTS {db_name}")

    def __init__(self, *, db_name=None, autocommit=False) -> None:
        self.db_name = db_name
        self.autocommit = autocommit
        self.dbi = None

    def connect(self):
        conninfo = psycopg.conninfo.make_conninfo(
            host=self.DB_HOST,
            port=self.DB_PORT,
            user=self.DB_USER,
            password=self.DB_PASSWORD,
            dbname=self.db_name or self.DB_NAME,
        )
        self.dbi = psycopg.connect(conninfo, autocommit=self.autocommit)
        return self

    def close(self):
        if self.dbi:
            self.dbi.close()

    def commit(self):
        self.dbi.commit()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_type is None:
            self.commit()
        self.close()

    def execute(self, query, **kwargs):
        return self.dbi.execute(query, params=kwargs)
    
    def cursor(self, *args, row_factory=namedtuple_row, **kwargs):
        return self.dbi.cursor(*args, row_factory=row_factory, **kwargs)

    def create_device(self, device_props):
        device_props = json.dumps(device_props) if device_props else None
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute(
                "INSERT INTO user_device (props) VALUES (%s) RETURNING id, uuid",
                (device_props,),
            )
            return cursor.fetchone()

    def get_device(self, *, id=None, uuid=None):
        sql = "SELECT * FROM user_device WHERE "
        if id:
            sql += "id=%s"
            args = [id]
        elif uuid:
            sql += "uuid=%s"
            args = [uuid]
        else:
            return None
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute(sql, args)
            return cursor.fetchone()

    def create_user_account(self):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute("INSERT INTO user_profile (username) VALUES (NULL) RETURNING id, uuid")
            user = cursor.fetchone()
            username = f"u{user.id}"
            cursor.execute("UPDATE user_profile SET username=%s WHERE id=%s RETURNING id, uuid, username, password_hash", (username, user.id))
            user = cursor.fetchone()
            return user

    def get_user(self, *, id=None, uuid=None, username=None):
        sql = "SELECT * FROM user_profile WHERE "
        if id:
            sql += "id=%s"
            args = [id]
        elif uuid:
            sql += "uuid=%s"
            args = [uuid]
        elif username:
            sql += "username=%s"
            args = [username]
        else:
            return None
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute(sql, args)
            return cursor.fetchone()

    def update_user_password(self, id, password_hash):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute("UPDATE user_profile SET password_hash=%s WHERE id=%s RETURNING id, uuid, username", (password_hash, id))
            return cursor.fetchone()

    def create_user_login(self, user_id, device_id):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute(
                "INSERT INTO user_login (user_id, device_id) VALUES (%s, %s) RETURNING id, uuid",
                (user_id, device_id),
            )
            return cursor.fetchone()
        
    def get_user_login(self, *, id=None, uuid=None):
        sql = "SELECT * FROM user_login WHERE "
        if id:
            sql += "id=%s"
            args = [id]
        elif uuid:
            sql += "uuid=%s"
            args = [uuid]
        else:
            return None
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute(sql, args)
            return cursor.fetchone()

    def close_user_login(self, *, uuid=None):
        if not uuid:
            return
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            self.dbi.execute("UPDATE user_login SET closed_ts=NOW() WHERE uuid=%s", (uuid,))

    def create_user_session(self, login_id):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute(
                "INSERT INTO user_session (login_id) VALUES (%s) RETURNING id, uuid",
                (login_id,),
            )
            return cursor.fetchone()

    def get_session_info(self, *, uuid):
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
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute(sql, (uuid,))
            return cursor.fetchone()

    def close_user_session(self, *, session_id, login_id):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            if session_id:
                self.dbi.execute("UPDATE user_session SET closed_ts=NOW() WHERE id=%s", (session_id,))
            if login_id:
                self.dbi.execute("UPDATE user_login SET closed_ts=NOW() WHERE id=%s", (login_id,))

    # CLUBS

    def create_club(self, *, founder_id, name):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute("INSERT INTO club (founder_id, name) VALUES (%s,%s) RETURNING *",(founder_id, name))
            club = cursor.fetchone()
            cursor.execute("INSERT INTO club_member (club_id, user_id, user_role, approved_ts, approved_by) VALUES (%s,%s,'OWNER',NOW(),0)",(club.id, founder_id))
            return club
        
    def get_club(self, club_id):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute("SELECT * FROM club WHERE id=%s",(club_id,))
            return cursor.fetchone()
        
    def get_club_members(self, club_id):
        sql = "SELECT u.*, x.user_role, x.approved_ts FROM club_member x JOIN user_profile u ON u.id=x.user_id WHERE x.club_id=%s"
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute(sql,(club_id,))
            return cursor.fetchall()

    def get_club_member(self, club_id, user_id):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute("SELECT * FROM club_member WHERE club_id=%s AND user_id=%s",(club_id,user_id))
            return cursor.fetchone()
        
    def update_club(self, club_id, *, name, description):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute("UPDATE club SET name=%s, description=%s WHERE id=%s RETURNING *",(name, description, club_id,))
            return cursor.fetchone()
        
    def get_clubs_for_user(self, *, user_id):
        sql = "SELECT c.*, u.user_role, u.approved_ts FROM club_member u JOIN club c ON c.id=u.club_id WHERE u.user_id=%s"
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute(sql,(user_id,))
            return cursor.fetchall()
        
    def create_join_club_request(self, *, club_id, user_id, user_role):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute("INSERT INTO club_member (club_id, user_id, user_role, approved_ts, approved_by) VALUES (%s,%s,%s,NOW(),0) RETURNING *",(club_id, user_id, user_role))
            return cursor.fetchone()
        
    # TABLES

    def create_table(self, *, club_id):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute("INSERT INTO poker_table (club_id) VALUES (%s) RETURNING *",(club_id,))
            return cursor.fetchone()

    def get_table(self, table_id):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute("SELECT * FROM poker_table WHERE id=%s",(table_id,))
            return cursor.fetchone()
        
    def get_tables_for_club(self, *, club_id):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute("SELECT * FROM poker_table WHERE club_id=%s",(club_id,))
            return cursor.fetchall()

    # temporary method to get list of tables
    def get_active_tables(self):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute("SELECT * FROM poker_table")
            return cursor.fetchall()
        
    # GAMES
    def game_begin(self, *, table_id, users):
        game = None
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute("INSERT INTO poker_game (table_id) VALUES (%s) RETURNING *",(table_id,))
            game = cursor.fetchone()
            params_seq = [(game.id, x.user_id) for x in users]
            cursor.executemany("INSERT INTO poker_game_user (game_id, user_id) VALUES (%s, %s)", params_seq)
        return game

    def game_end(self, game_id):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute("UPDATE poker_game SET end_ts=NOW() WHERE id=%s RETURNING *",(game_id,))
            return cursor.fetchone()
        
    def save_event(self, *, type, table_id, game_id=None, user_id=None, props: dict=None):
        if props:
            data = {}
            for k, v in props.items():
                if k in ('type', 'table_id', 'game_id'):
                    continue
                if k=='user_id' and user_id is not None:
                    continue
                data[k] = v
            data = json.dumps(data)
        else:
            data = None
        #logger.debug("%s %s %s %s save: %s", type, table_id, game_id, user_id, data)
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute("INSERT INTO poker_event (table_id, game_id, user_id, event_type, event_props) VALUES (%s, %s, %s, %s, %s) RETURNING id, event_ts",
                           (table_id, game_id, user_id, type, data))
            return cursor.fetchone()
        
