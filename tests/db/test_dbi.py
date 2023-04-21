from ravvi_poker_backend.db import DBI

class TEST_DBI(DBI):
    pass


def test_connect():
    dbi = TEST_DBI()
    dbi.connect()
    dbi.execute("SELECT %(a)s, %(b)s", a=1, b="abc")
    dbi.close()


def test_context():
    with TEST_DBI() as dbi:
        dbi.execute("SELECT %(a)s, %(b)s", a=1, b="abc")


def test_create_drop():
    dbi = TEST_DBI(autocommit=True)
    dbi.connect()
    dbi.execute("CREATE DATABASE test_create_drop TEMPLATE template0")
    dbi.execute("DROP DATABASE IF EXISTS test_create_drop")
    dbi.close()


def test_create_device():
    device_props = dict(
        name = 'TEST',
        model = 'TEST 1.0'
    )
    with TEST_DBI() as dbi:
        device0 = dbi.create_device(device_props)
        assert device0.id
        assert device0.uuid

    with TEST_DBI() as dbi:
        device = dbi.get_device(id = device0.id)
        assert device.id == device0.id
        assert device.uuid == device0.uuid
        assert device.created
        assert device.props


def test_create_user():
    with TEST_DBI() as dbi:
        user0 = dbi.create_user()
        assert user0.id
        assert user0.uuid

    with TEST_DBI() as dbi:
        user = dbi.get_user(id = user0.id)
        assert user.id == user0.id
        assert user.uuid == user0.uuid
        assert user.created
        assert hasattr(user, 'username')
        assert hasattr(user, 'password')

def test_register_user():
    device_props = dict(
        name = 'TEST',
        model = 'TEST 1.0'
    )
    with TEST_DBI() as dbi:
        user, device, login, session = dbi.register_user(None, device_props)
    assert user.uuid
    assert device.uuid
    assert login.uuid
    assert session.uuid

#if __name__ == "__main__":
#    test_connect()
