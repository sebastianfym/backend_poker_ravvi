from ravvi_poker_backend.db import DBI

DBI.db_name = 'tests'

def test_connect():
    db = DBI()
    db.connect()
    db.execute("SELECT %(a)s, %(b)s", a=1, b="abc")
    db.close()


def test_context():
    with DBI() as db:
        db.execute("SELECT %(a)s, %(b)s", a=1, b="abc")

def test_create_drop():
    db = DBI()
    db.connect(autocommit=True)
    db.execute("CREATE DATABASE test_create_drop TEMPLATE template0")
    db.execute("DROP DATABASE IF EXISTS test_create_drop")
    db.close()


if __name__ == "__main__":
    test_connect()
