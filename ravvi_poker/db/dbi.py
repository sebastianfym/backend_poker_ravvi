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

    def deactivate_user(self, user_id):
        sql = """
            UPDATE user_session
            SET closed_ts=NOW()
            WHERE login_id in (
                SELECT id
                FROM user_login
                WHERE user_id=%s
            )
            """
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute(sql, (user_id,))
            cursor.execute("UPDATE user_login SET closed_ts=NOW() WHERE user_id=%s", (user_id,))
            cursor.execute("UPDATE user_profile SET closed_ts=NOW() WHERE id=%s", (user_id,))

    def update_user_profile(self, user_id, **kwargs):
        params = ", ".join([f"{key}=%s" for key in kwargs])
        values = list(kwargs.values()) + [user_id]
        sql = f"UPDATE user_profile SET {params} WHERE id=%s RETURNING *"
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute(sql, values)
            return cursor.fetchone()

    # IMAGES

    def get_user_images(self, owner_id, id=None, uuid=None, image_data=None):
        args = [owner_id]
        sql = "SELECT * FROM image WHERE (owner_id=%s or owner_id is NULL)"
        if id:
            args.append(id)
            sql += " and id=%s"
        if uuid:
            args.append(uuid)
            sql += " and uuid=%s"
        if image_data:
            args.append(image_data)
            sql += " and image_data=%s"
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute(sql, args)
            if len(args) > 1:
                return cursor.fetchone()
            return cursor.fetchall()

    def create_user_image(self, owner_id, image_data, mime_type):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute("INSERT INTO image (owner_id, image_data, mime_type) VALUES (%s, %s, %s) RETURNING *", (owner_id, image_data, mime_type))
            return cursor.fetchone()

    def delete_image(self, image_id):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute("DELETE FROM image WHERE id=%s", (image_id,))

    # CLUBS

    def create_club(self, *, founder_id, name, description, image_id):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute("INSERT INTO club (founder_id, name, description, image_id) VALUES (%s,%s,%s,%s) RETURNING *",(founder_id, name, description, image_id))
            club = cursor.fetchone()
            cursor.execute("INSERT INTO club_member (club_id, user_id, user_role, approved_ts, approved_by) VALUES (%s,%s,'OWNER',NOW(),0)",(club.id, founder_id))
            return club

    def get_club(self, club_id):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute("SELECT * FROM club WHERE id=%s",(club_id,))
            return cursor.fetchone()

    def update_club(self, club_id, **kwargs):
        params = ", ".join([f"{key}=%s" for key in kwargs])
        values = list(kwargs.values()) + [club_id]
        sql = f"UPDATE club SET {params} WHERE id=%s RETURNING *"
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute(sql, values)
            return cursor.fetchone()

    def get_clubs_for_user(self, *, user_id):
        sql = "SELECT c.*, u.user_role, u.approved_ts FROM club_member u JOIN club c ON c.id=u.club_id WHERE u.user_id=%s"
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute(sql,(user_id,))
            return cursor.fetchall()

    def delete_club(self, club_id):
        # TODO вернуться после утверждения жизненных циклов стола и участника клуба 
        pass

    def create_join_club_request(self, *, club_id, user_id, user_role):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute("INSERT INTO club_member (club_id, user_id, user_role, approved_ts, approved_by) VALUES (%s,%s,%s,NULL,NULL) RETURNING *",(club_id, user_id, user_role))
            return cursor.fetchone()

    def approve_club_member(self, club_id, user_id, member_id):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute("UPDATE club_member SET approved_ts=NOW(), approved_by=%s WHERE club_id=%s AND user_id=%s RETURNING *",(user_id, club_id, member_id))
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

    def delete_club_member(self, club_id, member_id):
        # TODO вернуться после утверждения жизненных циклов стола и участника клуба
        pass

    # TABLES

    def create_table(self, club_id, **kwargs):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            fields = ", ".join(["club_id"] + list(kwargs.keys()))
            values = [club_id] + list(kwargs.values())
            values_pattern = ", ".join(["%s"] * len(values))
            sql = f"INSERT INTO poker_table ({fields}) VALUES ({values_pattern}) RETURNING *"
            cursor.execute(sql, values)
            return cursor.fetchone()

    def get_table(self, table_id):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute("SELECT * FROM poker_table WHERE id=%s",(table_id,))
            return cursor.fetchone()

    def get_tables_for_club(self, *, club_id):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute("SELECT * FROM poker_table WHERE club_id=%s",(club_id,))
            return cursor.fetchall()

    def delete_table(self, table_id):
        # TODO дождаться определения жизненного цикла стола
        pass

    # temporary method to get list of tables
    def get_active_tables(self):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute("SELECT * FROM poker_table")
            return cursor.fetchall()
        
    # GAMES
    def game_begin(self, *, table_id, user_ids):
        game = None
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute("INSERT INTO poker_game (table_id) VALUES (%s) RETURNING *",(table_id,))
            game = cursor.fetchone()
            params_seq = [(game.id, user_id) for user_id in user_ids]
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

    def get_game(self, game_id):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute("SELECT * FROM poker_game WHERE id=%s",(game_id,))
            return cursor.fetchone()

    # DEBUG
    def create_debug_message(self, user_id, game_id, table_id, debug_message):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute("INSERT INTO debug (user_id, game_id, table_id, debug_message) VALUES (%s,%s,%s,%s) RETURNING *",
                           (user_id,game_id,table_id,debug_message,))
            return cursor.fetchone()

    def get_debug_messages(self, user_id):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute("SELECT * FROM debug WHERE user_id=%s",(user_id,))
            return cursor.fetchall()
