import asyncio
from ravvi_poker.client.client import PokerClient, Message


class MyVerySmartCustomPokerStrategy:
    def __init__(self, client: PokerClient) -> None:
        self.client = client

    async def __call__(self, msg: Message):
        await self.client.play_check_or_fold(msg)


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
        print('Получил запрос, сейчас всё сделаю')
        await client.up_club_balance(club_id=my_club_id, amount=50000)
        while True:
            await asyncio.sleep(2)
            requests = await client.get_club_chips_requests(my_club_id)
            if len(requests[1]['users_requests']) != 0:
                print('Пополнил')
                await client.accept_all_balance_requests(my_club_id)
                break
        await asyncio.sleep(2)
        # Создаём столы
        print('Тогда создам столы для игры')
        for table in range(10): #Случайное число
            await client.create_table(club_id=my_club_id, table_type="RG", table_name=None,
                                      table_seats=9, game_type="NLH",
                                      game_subtype="REGULAR", buyin_cost=1.0)
        await asyncio.sleep(1)
        print('Столы готовы, садись играть ')


async def player_scenario():
    client = PokerClient()
    strategy = MyVerySmartCustomPokerStrategy(client)
    async with client:
        await client.auth_register()
        await client.update_user_profile(name=f'PLAYER-{client.user_id}', image_id=12)
        await client.password_update(None, "password")
        await client.login_with_username_and_password(username=f'PLAYER-{client.user_id}', password="password")
        await client.get_user_by_id(id=client.user_id)
        await asyncio.sleep(1)
        club = await client.send_req_join_in_club(club_id=1001, user_comment=None)
        await client.send_req_to_up_user_balance(club[1].id, 5100)
        print('Отправил запрос')
        while True:
            await asyncio.sleep(1)
            member_profile = await client.get_detail_member_info(club_id=club[1].id)
            if member_profile[1].balance and member_profile[1].balance > 0:
                print('Деньги пришли, гуляем на все')
                break




async def main():
    await asyncio.gather(owner_scenario(), player_scenario(), return_exceptions=True)


if __name__ == '__main__':
    asyncio.run(main())
