import pytest

from ravvi_poker.engine.events import Command

def test_events_command():

    with pytest.raises(TypeError):
        x = Command()
    with pytest.raises(TypeError):
        x = Command(table_id=111)
    with pytest.raises(TypeError):
        x = Command(table_id=111, cmd_type=222)

    expected_keys = ['table_id', 'cmd_type', 'client_id', 'props']

    x = Command(123, table_id=111, cmd_type=222, client_id=333)
    assert set(x.keys()) == set(expected_keys)
    assert x.id == 123
    assert x.client_id == 333
    assert x.table_id == 111
    assert x.cmd_type == 222
    assert x.props == dict()

    x = Command(table_id=111, cmd_type=222, client_id=333, a=1, b=2)
    assert x.id is None
    assert x.client_id == 333
    assert x.table_id == 111
    assert x.cmd_type == 222
    assert x.props == dict(a=1, b=2)
    assert x.a == 1
    assert x.b == 2
