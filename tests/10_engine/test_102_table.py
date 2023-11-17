import pytest
from ravvi_poker.engine.table import Table, User

class Table_X(Table):
    
    def __init__(self, id):
        super().__init__(id, table_type='RING_GAME', table_seats=9, game_type='TEST', game_subtype='01')
        self._event = None
        self._take_seat_enabled = False

    @property
    def take_seat_enabled(self):
        return self._take_seat_enabled

    async def user_factory(self, user_id):
        user = self.users.get(user_id, None)
        if not user:
            username='u'+str(user_id)
            user = User(id=user_id, username=username)
            self.users[user_id] = user
        return user

    async def emit_event(self, event):
        self._event = event

    async def on_user_join(self, user):
        pass

    async def on_player_enter(self, user, user_seat_idx):
        user.balance = 100

    async def on_user_exit(self, user):
        pass

    async def on_user_leave(self, user):
        pass


def test_1021_table_info():
    table = Table_X(1)
    info = table.get_table_info(777)

    assert info['table_id'] == 1

    print(info)

@pytest.mark.asyncio
async def test_102_1_user_join_no_seat():
    table = Table_X(1)
    assert not table.users

    table._take_seat_enabled = False
    await table.handle_cmd_join(user_id=1, client_id=10, take_seat=False)

    user, seat_idx, _ = table.find_user(1)
    assert user
    assert user.balance == 0
    assert user.connected
    assert user.clients == {10}
    assert seat_idx is None
    assert all(s is None for s in table.seats)
    print(table._event)


    table._take_seat_enabled = True
    await table.handle_cmd_join(user_id=1, client_id=11, take_seat=False)

    user, seat_idx, _ = table.find_user(1)
    assert user
    assert user.balance == 0
    assert user.connected
    assert user.clients == {10,11}
    assert seat_idx is None
    assert all(s is None for s in table.seats)
    print(table._event)

    table._take_seat_enabled = False
    await table.handle_cmd_join(user_id=1, client_id=12, take_seat=True)

    user, seat_idx, _ = table.find_user(1)
    assert user
    assert user.balance == 0
    assert user.connected
    assert user.clients == {10,11,12}
    assert seat_idx is None
    assert all(s is None for s in table.seats)
    print(table._event)

    await  table.handle_cmd_leave(user_id=1, client_id=11)
    user, seat_idx, _ = table.find_user(1)
    assert user
    assert user.balance == 0
    assert user.connected
    assert user.clients == {10,12}
    assert seat_idx is None
    assert all(s is None for s in table.seats)

    await table.handle_cmd_leave(user_id=1, client_id=10)
    user, seat_idx, _ = table.find_user(1)
    assert user
    assert user.balance == 0
    assert user.connected
    assert user.clients == {12}
    assert seat_idx is None
    assert all(s is None for s in table.seats)

    await table.handle_cmd_leave(user_id=1, client_id=13)
    user, seat_idx, _ = table.find_user(1)
    assert user
    assert user.balance == 0
    assert user.connected
    assert user.clients == {12}
    assert seat_idx is None
    assert all(s is None for s in table.seats)

    await table.handle_cmd_leave(user_id=1, client_id=12)
    user, seat_idx, _ = table.find_user(1)
    assert user is None
    assert seat_idx is None
    assert all(s is None for s in table.seats)
    assert not table.users

    await table.handle_cmd_leave(user_id=1, client_id=None)
    user, seat_idx, _ = table.find_user(1)
    assert user is None
    assert seat_idx is None
    assert all(s is None for s in table.seats)
    assert not table.users

@pytest.mark.asyncio
async def test_102_2_user_join_take_seat():
    table = Table_X(2)
    table._take_seat_enabled = True
    assert not table.users

    await table.handle_cmd_join(user_id=2, client_id=21, take_seat=True)

    user, seat_idx, _ = table.find_user(2)
    assert user
    assert user.balance == 100
    assert user.connected
    assert user.clients == {21}
    assert seat_idx == 0
    assert table.seats[seat_idx] == user

    await table.handle_cmd_join(user_id=2, client_id=22, take_seat=True)

    user, seat_idx, _ = table.find_user(2)
    assert user
    assert user.balance == 100
    assert user.connected
    assert user.clients == {21, 22}
    assert seat_idx == 0
    assert table.seats[seat_idx] == user

    await table.handle_cmd_join(user_id=2, client_id=23, take_seat=True)

    user, seat_idx, _ = table.find_user(2)
    assert user
    assert user.balance == 100
    assert user.connected
    assert user.clients == {21, 22, 23}
    assert seat_idx == 0
    assert table.seats[seat_idx] == user

    await table.handle_cmd_join(user_id=3, client_id=31, take_seat=True)

    user, seat_idx, _ = table.find_user(3)
    assert user
    assert user.balance == 100
    assert user.connected
    assert user.clients == {31}
    assert seat_idx == 1
    assert table.seats[seat_idx] == user

@pytest.mark.asyncio
async def test_102_3_user_move_seat():
    table = Table_X(2)
    table._take_seat_enabled = True
    assert not table.users
    
    await table.handle_cmd_join(user_id=3, client_id=31, take_seat=False)

    user, seat_idx, _ = table.find_user(3)
    assert user
    assert user.balance == 0
    assert user.connected
    assert user.clients == {31}
    assert seat_idx is None

    await table.handle_cmd_take_seat(user_id=3, new_seat_idx=3)
    assert table._event.type == 201

    user, seat_idx, _ = table.find_user(3)
    assert user
    assert user.balance == 0
    assert user.connected
    assert user.clients == {31}
    assert seat_idx==3
    assert table.seats[seat_idx] == user

    await table.handle_cmd_take_seat(user_id=3, new_seat_idx=1)
    assert table._event.type == 202

    user, seat_idx, _ = table.find_user(3)
    assert user
    assert user.balance == 0
    assert user.connected
    assert user.clients == {31}
    assert seat_idx==1
    assert table.seats[seat_idx] == user

    # invalid seat
    table._event = None
    await table.handle_cmd_take_seat(user_id=3, new_seat_idx=666)
    assert table._event is None

    # invalid user
    table._event = None
    await table.handle_cmd_take_seat(user_id=666, new_seat_idx=666)
    assert table._event is None



if __name__=='__main__':
    import asyncio
    asyncio.run(test_102_1_user_join_no_seat())
    asyncio.run(test_102_2_user_join_take_seat())
    asyncio.run(test_102_3_user_move_seat())