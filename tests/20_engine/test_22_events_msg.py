import pytest

from ravvi_poker.engine.events import Message

def test_message():

    assert Message.Type.verify(101)
    assert Message.Type.verify(Message.Type.TABLE_INFO)
    assert Message.Type.decode('TABLE_INFO') == Message.Type.TABLE_INFO
    assert Message.Type.decode(101) == Message.Type.TABLE_INFO

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

    x2 = x.clone()

    assert x2.id is None
    assert x2.table_id == 111
    assert x2.msg_type == 222
    assert x2.props == dict(a=1, b=2)
    assert x2.client_id == 333
    assert x2.cmd_id == 444
    assert x2.a == 1
    assert x2.b == 2

def test_message_private_info():
    users=[
        dict(user_id=10, cards_open=False, cards=[11,12], hand_type='A', hand_cards=[11,12,13,14,15]),
        dict(user_id=20, cards_open=True, cards=[21,22], hand_type='B', hand_cards=[21,22,23,24,25]),
        dict(user_id=30, cards_open=False, cards=[31,32], hand_type='C', hand_cards=[31,32,33,34,35]),
    ]

    # TABLE_INFO
    x = Message(id=1, msg_type=Message.Type.TABLE_INFO, table_id=777, client_id=100, table_redirect_id=777, users=users)

    msg = x.hide_private_info(for_user_id=10)

    assert msg.users[0] == {'user_id': 10, 'cards': [11, 12], 'hand_type': 'A', 'hand_cards': [11, 12, 13, 14, 15]}
    assert msg.users[1] == {'user_id': 20, 'cards': [21, 22], 'hand_type': 'B', 'hand_cards': [21, 22, 23, 24, 25]}
    assert msg.users[2] == {'user_id': 30, 'cards': [0, 0]}

    # PLAYER_CARDS
    x = Message(id=2, msg_type=Message.Type.PLAYER_CARDS, table_id=777, **users[0])
    
    msg = x.hide_private_info(for_user_id=10)
    assert msg.user_id == 10
    assert msg.cards == [11, 12]
    assert msg.hand_type and msg.hand_cards

    x = Message(msg_type=Message.Type.PLAYER_CARDS, table_id=777, **users[1])

    msg = x.hide_private_info(for_user_id=10)
    assert msg.user_id == 20
    assert msg.cards == [21, 22]
    assert msg.hand_type and msg.hand_cards

    x = Message(msg_type=Message.Type.PLAYER_CARDS, table_id=777, **users[2])

    msg = x.hide_private_info(for_user_id=10)
    assert msg.user_id == 30
    assert msg.cards == [0, 0]
    assert not msg.hand_type and not msg.hand_cards

    # PLAYER_MOVE
    x = Message(msg_type=Message.Type.GAME_PLAYER_MOVE, table_id=777, user_id=10, options=[1,2,3])
    msg = x.hide_private_info(for_user_id=10)
    assert msg.user_id == 10
    assert msg.options == [1,2,3]

    x = Message(msg_type=Message.Type.GAME_PLAYER_MOVE, table_id=777, user_id=30, options=[1,2,3])
    msg = x.hide_private_info(for_user_id=10)
    assert msg.user_id == 30
    assert not msg.options


    x = Message(msg_type=Message.Type.GAME_BEGIN, table_id=777)
    msg = x.hide_private_info(for_user_id=10)




