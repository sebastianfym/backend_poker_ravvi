import psycopg
from .dbi import DBI

def create_database(db_name):
    conninfo = DBI.conninfo('postgres')
    with psycopg.connect(conninfo, autocommit=True) as dbi:
        with dbi.cursor() as cur:
            dbi.execute(f"CREATE DATABASE {db_name} TEMPLATE template0")

def drop_database(db_name):
    conninfo = DBI.conninfo('postgres')
    with psycopg.connect(conninfo, autocommit=True) as dbi:
        with dbi.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS {db_name}")

def apply_sql_files(db_name, sql_files):
    conninfo = DBI.conninfo(db_name)
    with psycopg.connect(conninfo, autocommit=False) as dbi:
        for name, sql in sql_files:
            print("===", name, "===")
            sql = sql.replace("%", "%%")
            dbi.execute(sql)
        dbi.commit()
