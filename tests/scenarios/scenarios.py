import asyncio
from ravvi_poker.client.client import PokerClient, Message
from ravvi_poker.engine.events import MessageType


class MyVerySmartCustomPokerStrategy:
    def __init__(self, client: PokerClient, club_id=None) -> None:
        self.client = client
        self.club_id = club_id

    async def __call__(self, msg: Message):
        await self.client.play_check_or_fold_or_allin(msg)



async def owner_scenario():
    client = PokerClient()
    strategy = MyVerySmartCustomPokerStrategy(client)
    async with client:
        await client.auth_register()
        await client.update_user_profile(name=f'OWNER-{client.user_id}', image_id=12)
        await client.password_update(None, "password")
        await client.login_with_username_and_password(username=f'OWNER-{client.user_id}', password="password")
        await client.get_user_by_id(id=client.user_id)
        my_club = await client.create_club(name=None, description=None, image_id=None, user_role="O",
                                           user_approved=False, timezone=None)
        my_club_id = my_club[1].id
        await client.update_club(club_id=my_club_id, description='my best club', image_id=12,
                                 timezone="Europe/Moscow", automatic_confirmation=True)
        await client.up_club_balance(club_id=my_club_id, amount=50000)
        while True:
            await asyncio.sleep(2)
            requests = await client.get_club_chips_requests(my_club_id)
            if len(requests[1]['users_requests']) != 0:
                await client.accept_all_balance_requests(my_club_id)
                break
        await asyncio.sleep(1)
        # Создаём столы
        # for table in range(10):  # Случайное число
        #     await client.create_table(club_id=my_club_id, table_type="RG", table_name=None,
        #                               table_seats=9, game_type="NLH",
        #                               game_subtype="REGULAR", buyin_cost=1.0, blind_small=1.0, blind_big=10.0,
        #                               buyin_value=10.0, buyin_min=10.0)
        await client.create_table(club_id=my_club_id, table_type="RG", table_name=None,
                                  table_seats=9, game_type="NLH",
                                  game_subtype="REGULAR", buyin_cost=15.0, blind_small=3.0, blind_big=13.0,
                                  buyin_value=1.0, buyin_min=19.0)
        await asyncio.sleep(1)


async def player_scenario():
    client = PokerClient()
    strategy = MyVerySmartCustomPokerStrategy(client, club_id=1004) #Todo тут нужно подставлять  id актуального клуба
    async with client:
        # await client.auth_register()
        # await client.update_user_profile(name=f'PLAYER-{client.user_id}', image_id=12)
        # await client.password_update(None, "password")
        await client.login_with_username_and_password(username=f'preflop bill', password="Y8G5Qv3b")#(username=f'PLAYER-{client.user_id}', password="password")
        await client.get_user_by_id(id=client.user_id)
        await asyncio.sleep(1)

        club = await client.send_req_join_in_club(club_id=1004, user_comment=None) #Todo тут нужно подставлять  id актуального клуба
        print(f"club: {club}")
        club_id = 1004
        # club_id = club[1].id
        #
        # chips_request = await client.send_req_to_up_user_balance(club_id, 5100)
        # if chips_request[0] == 201:
        #     while True:
        #         await asyncio.sleep(1)
        #         member_profile = await client.get_detail_member_info(club_id=club_id)
        #         if member_profile[1].balance and member_profile[1].balance > 0:
        #             break
        # else:
        #     raise RuntimeError("Failed to chips request")

        await asyncio.sleep(3)

        # for table in (await client.get_club_tables(club_id))[1]:
        #     await client.join_table(table_id=table.id, take_seat=True, table_msg_handler=strategy, club_id=club_id)
        #     await asyncio.sleep(180)

        table = (await client.get_club_tables(club_id))[1]
        while True:
            await client.join_table(table_id=table[0].id, take_seat=True, table_msg_handler=strategy, club_id=club_id)
            await asyncio.sleep(30)




async def main():
    # await asyncio.gather(owner_scenario(), player_scenario(), player_scenario(), return_exceptions=True)
    await player_scenario()


if __name__ == '__main__':
    asyncio.run(main())
