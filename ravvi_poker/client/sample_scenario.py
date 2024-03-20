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


async def sample_scenario():
    client = PokerClient()
    strategy = MyVerySmartCustomPokerStrategy(client)
    async with client:
        # регистрируемся в приложении
        await client.auth_register()
        # обновляем аккаунт
        await client.update_user_profile(name='Bogdan23', image_id=12)

        # Смотрим профиль по id
        await client.get_user_by_id(id=client.user_id)
        # Получаем список доступных картинок
        await client.get_available_images()
        # Создаем клуб
        my_club = await client.create_club(name=None, description=None, image_id=None, user_role="O", user_approved=False, timezone=None)
        # Получить клуб по id
        await client.get_club_by_id(club_id=my_club.id)
        # Обновляем клуб
        await client.update_club(club_id=my_club.id, name="Bogdan club", description='my best club', image_id=12, timezone="Europe/Moscow", automatic_confirmation=True)
        # Получить список клубов для текущего пользователя
        await client.get_all_clubs()
        # Получить список участников клуба
        await client.get_clubs_members(my_club.id)
        # Отправить заявку на вступление в клуб
        await client.send_req_join_in_club(club_id=my_club.id, user_comment='Comment')
        # Создаем стол клуба
        await client.create_table(club_id=my_club.id, table_type="SNG", table_name="ClubTable", table_seats=9, game_type="NLH", game_subtype="REGULAR", buyin_cost=10)
        # Получение списка столов
        await client.get_club_tables(my_club.id)
        # Получение детального представления участника клуба для владельца
        await client.get_member_info_for_owner(my_club.id, client.user_id)
        # Получение своей анкеты участника в клубе
        await client.get_detail_member_info(my_club.id)
        # Получение баланса клуба
        await client.get_club_balance(my_club.id)
        # Получение списка запросов на пополнение баланса
        await client.get_club_chips_requests(my_club.id)
        # Получение разделения уровней блайндов
        await client.levels_schedule(table_type="SNG")
        # Получение информации о распределении вознаграждений
        await client.rewards_distribution()
        # Получение списка стран
        await client.countries(language='ru')
        # # открываем стол (произвольный для примера)
        # await client.join_table(13, True, strategy)
        # # и играем 5 мин
        # await asyncio.sleep(5*60)
        # # закрывем стол
        # await client.exit_table(13)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(sample_scenario())


