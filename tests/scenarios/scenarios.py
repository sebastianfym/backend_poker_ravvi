import asyncio
from ravvi_poker.client.client import PokerClient, Message


class MyVerySmartCustomPokerStrategy:
    def __init__(self, client: PokerClient) -> None:
        self.client = client

    async def __call__(self, msg: Message):
        await self.client.play_check_or_fold(msg)


async def owner_scenario(event, event_2):
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
        await client.update_club(club_id=my_club[1].id, description='my best club', image_id=12,
                                 timezone="Europe/Moscow", automatic_confirmation=True)

        await event.wait()  # ждем событие от player_scenario()
        await client.up_club_balance(club_id=my_club[1].id, amount=50000)
        # В этот момент второй сценарий уже должен быть выполнен

        while True:
            requests = await client.get_club_chips_requests(my_club[1].id)
            if len(requests[1]['users_requests']) != 0:
                await client.accept_all_balance_requests(my_club[1].id)
                event_2.set()  # устанавливаем событие event_2
                break


async def player_scenario(event, event_2):
    client = PokerClient()
    strategy = MyVerySmartCustomPokerStrategy(client)
    async with client:
        await client.auth_register()
        await client.update_user_profile(name=f'PLAYER-{client.user_id}', image_id=12)
        await client.password_update(None, "password")
        await client.login_with_username_and_password(username=f'PLAYER-{client.user_id}', password="password")
        await client.get_user_by_id(id=client.user_id)
        await asyncio.sleep(1)
        club = await client.send_req_join_in_club(club_id=1013, user_comment=None)
        await client.send_req_to_up_user_balance(club[1].id, 5100)
        event.set()  # устанавливаем событие event
        await event_2.wait()  # Ожидаем установки события event_2
        while True:
            await asyncio.sleep(1)
            member_profile = await client.get_detail_member_info(club_id=club[1].id)
            if member_profile[1].balance and member_profile[1].balance > 0:
                break


async def main():
    event = asyncio.Event()
    event_2 = asyncio.Event()
    await asyncio.gather(owner_scenario(event, event_2), player_scenario(event, event_2), return_exceptions=True)


if __name__ == '__main__':
    asyncio.run(main())
