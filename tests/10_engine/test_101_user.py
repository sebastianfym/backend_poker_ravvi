from ravvi_poker.engine.user import User

def test_101_1_user():
    user = User(777, 'test')
    assert user.id == 777
    #assert user.username == 'test'
    #assert user.image_id is None
    assert user.balance == 0
    assert len(user.clients) == 0
    assert user.connected == False

    user.clients.add(111)
    assert user.connected == True

    info = user.get_info()
    assert info['user_id'] == 777
    #assert info['username'] == 'test'