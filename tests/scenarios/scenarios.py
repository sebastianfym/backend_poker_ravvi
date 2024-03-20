import logging
import asyncio
from ravvi_poker.client.client import PokerClient, Message


class MyVerySmartCustomPokerStrategy:

    def __init__(self, client: PokerClient) -> None:
        # инициализация игровой стратегии
        self.client = client

    async def __call__(self, msg: Message):
        # обработка игровых событий
        await self.client.play_check_or_fold(msg)


async def owner_scenario():
    client = PokerClient()
    strategy = MyVerySmartCustomPokerStrategy(client)
    async with client:
        # регистрируемся в приложении
        await client.auth_register()
        # обновляем аккаунт
        await client.update_user_profile(name=f'OWNER-{client.user_id}', image_id=12)
        # Устанавливаем пароль
        await client.password_update(None, "password")
        # Логинимся
        await client.login_with_username_and_password({client.user_id}, "password")
        # Смотрим профиль по id
        await client.get_user_by_id(id=client.user_id)
        # Создаем клуб
        my_club = await client.create_club(name=None, description=None, image_id=None, user_role="O",
                                           user_approved=False, timezone=None)
        # Обновляем клуб и даем возможность вступать автоматически
        await client.update_club(club_id=my_club.id, name="Bogdan club", description='my best club', image_id=12,
                                 timezone="Europe/Moscow", automatic_confirmation=True)
        # Пополняем баланс клуба
        await client.up_club_balance(club_id=my_club.id, amount=50000)
        # Создаем стол клуба
        for i in range(10):
            await client.create_table(club_id=my_club.id, table_type="SNG", table_name=f"ClubTable{i}", table_seats=9,
                                  game_type="NLH", game_subtype="REGULAR", buyin_cost=10)
        # Отслеживаем новые  заявки на пополнение
        while True:
            requests = await client.get_club_chips_requests(my_club.id)
            if len(requests['club_members']) != 0:
                break
        # Одобряем все запросы на пополнение
        await client.accept_all_balance_requests(my_club.id)


async def player_scenario():
    client = PokerClient()
    strategy = MyVerySmartCustomPokerStrategy(client)
    async with client:
        # регистрируемся в приложении
        await client.auth_register()
        # обновляем аккаунт
        await client.update_user_profile(name=f'OWNER-{client.user_id}', image_id=12)
        # Устанавливаем пароль
        await client.password_update(None, "password")
        # Логинимся
        await client.login_with_username_and_password({client.user_id}, "password")
        # Смотрим профиль по id
        await client.get_user_by_id(id=client.user_id)
        # Отправляем заявку на вступление в клуб (сейчас стоит примерный id)
        club = await client.send_req_join_in_club(club_id=1000, user_comment=None)
        # Отправляем запрос на пополнение баланса
        await client.send_req_to_up_user_balance(club.id, 2500)
        # Проверяем, что баланс пополнен
        while True:
            member_profile = await client.get_detail_member_info(club_id=club.id)
            if member_profile.balance and member_profile.balance > 0:
                break
        # Получаем список столов
        tables = await client.get_club_tables(club.id)
        for table in tables:
            try:
                await client.join_table(table.id, True, 11)
                await strategy.client.play_check_or_fold()
            except:
                continue

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(owner_scenario())
    asyncio.sleep(5)
    asyncio.run(player_scenario())