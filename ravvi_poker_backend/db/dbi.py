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
    
