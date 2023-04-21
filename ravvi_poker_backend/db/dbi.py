import os
import json
import psycopg
from psycopg.rows import namedtuple_row


class DBI:
    
    DB_HOST = os.getenv("RAVVI_POKER_DB_HOST", "localhost")
    DB_PORT = int(os.getenv("RAVVI_POKER_DB_PORT", "15432"))
    DB_USER = os.getenv("RAVVI_POKER_DB_USER", "postgres")
    DB_PASSWORD = os.getenv("RAVVI_POKER_DB_PASSWORD", "password")
    DB_NAME = os.getenv("RAVVI_POKER_DB_NAME", 'tests')

    @classmethod
    def create_database(cls, db_name):
        conninfo = psycopg.conninfo.make_conninfo(
            host=cls.DB_HOST, port=cls.DB_PORT, user=cls.DB_USER, password=cls.DB_PASSWORD,
            dbname='postgres',
        )
        with psycopg.connect(conninfo, autocommit=True) as dbi:
            with dbi.cursor() as cur:
                dbi.execute(f"CREATE DATABASE {db_name} TEMPLATE template0")


    @classmethod
    def drop_database(cls, db_name):
        conninfo = psycopg.conninfo.make_conninfo(
            host=cls.DB_HOST, port=cls.DB_PORT, user=cls.DB_USER, password=cls.DB_PASSWORD,
            dbname='postgres',
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
    
    def create_device(self, device_props):
        device_props = json.dumps(device_props) if device_props else None
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute('INSERT INTO user_device (props) VALUES (%s) RETURNING id, uuid', (device_props,));
            return cursor.fetchone()
        
    def get_device(self, id):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute('SELECT * FROM user_device WHERE id=%s', (id,));
            return cursor.fetchone()

    def create_user(self):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute('INSERT INTO user_account (username, password) VALUES (null, null) RETURNING id, uuid');
            return cursor.fetchone()

    def get_user(self, id):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute('SELECT * FROM user_account WHERE id=%s', (id,));
            return cursor.fetchone()

    def create_user_login(self, user_id, device_id):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute('INSERT INTO user_login (user_id, device_id) VALUES (%s, %s) RETURNING id, uuid', (user_id, device_id));
            return cursor.fetchone()

    def create_user_session(self, user_login_id):
        with self.dbi.cursor(row_factory=namedtuple_row) as cursor:
            cursor.execute('INSERT INTO user_session (user_login_id) VALUES (%s) RETURNING id, uuid', (user_login_id,));
            return cursor.fetchone()
        
    def register_user(self, device_uuid, device_props):
        user = self.create_user()
        device = self.create_device(device_props)
        login = self.create_user_login(user.id, device.id)
        session = self.create_user_session(login.id)
        return user, device, login, session
            

