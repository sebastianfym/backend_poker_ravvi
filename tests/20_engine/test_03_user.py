from ravvi_poker.engine.user import User

def test_engine_user():
    user = User(777, 'test', 999)
    assert user.id == 777
    assert user.name == 'test'
    assert user.image_id == 999
    assert user.balance is None
    assert len(user.clients) == 0
    assert user.connected == False

    user.clients.add(111)
    assert user.connected == True

    info = user.get_info()
    assert info['id'] == 777
    assert info['name'] == 'test'
    assert info['image_id'] == 999
