import os
import psycopg


class DBI:
    db_host = os.getenv("RAVVI_POKER_DB_HOST", "localhost")
    db_port = int(os.getenv("RAVVI_POKER_DB_PORT", "15432"))
    db_user = os.getenv("RAVVI_POKER_DB_USER", "postgres")
    db_password = os.getenv("RAVVI_POKER_DB_PASSWORD", "password")
    db_name = os.getenv("RAVVI_POKER_DB_NAME", 'tests')

    def __init__(self) -> None:
        self.dbi = None

    def connect(self, *, host=None, port=None, user=None, password=None, db_name=None, autocommit=False):
        conninfo = psycopg.conninfo.make_conninfo(
            host=host or self.db_host,
            port=port or self.db_port,
            user=user or self.db_user,
            password=password or self.db_password,
            dbname=db_name or self.db_name,
        )
        self.dbi = psycopg.connect(conninfo, autocommit=autocommit)
        return self

    def close(self):
        if self.dbi:
            self.dbi.close()

    def __enter__(self):
        return self.connect()

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close()

    def execute(self, query, **kwargs):
        return self.dbi.execute(query, params=kwargs)
    
    def commit(self):
        self.dbi.commit()
