import pytest

from ravvi_poker.engine.events import Message

def test_events_message():

    with pytest.raises(TypeError):
        x = Message()

    expected_keys = ['table_id', 'game_id', 'msg_type', 'cmd_id', 'client_id', 'props']

    x = Message(123, table_id=111, msg_type=222, client_id=333)
    assert set(x.keys()) == set(expected_keys)
    assert x.id == 123
    assert x.table_id == 111
    assert x.msg_type == 222
    assert x.props == dict()
    assert x.client_id == 333
    assert x.cmd_id is None

    x = Message(table_id=111, msg_type=222, client_id=333, cmd_id=444, a=1, b=2)
    assert x.id is None
    assert x.table_id == 111
    assert x.msg_type == 222
    assert x.props == dict(a=1, b=2)
    assert x.client_id == 333
    assert x.cmd_id == 444
    assert x.a == 1
    assert x.b == 2
