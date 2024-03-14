import logging
import asyncio
from .client import PokerClient, Message

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
        # открываем стол
        await client.join_table(13, True, strategy)
        # и играем 5 мин
        await asyncio.sleep(5*60)
        # закрывем стол
        await client.exit_table(13)

if __name__=='__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(sample_scenario())


