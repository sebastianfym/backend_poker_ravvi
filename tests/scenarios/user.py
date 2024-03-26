import logging
import asyncio
from ravvi_poker.client import PokerClient

async def try_to_register(client: PokerClient, *,  sleep_min = 2, sleep_max = 5):
    """Регистрация пользователя с несколькими попытками и настройка профиля"""
    for _ in range(1):
        await  client.sleep_random(sleep_min, sleep_max)
        status, _ = await client.auth_register()
        if status==200:
            break
    if status!=200:
        raise RuntimeError("Failed to register user")

    username = f"T-{client.user_id}"
    password = f"test{client.user_id}"

    await client.sleep_random(sleep_min, sleep_max)
    status, _ = await client.password_update("", password)
    if status!=200:
        raise RuntimeError("Failed to set password")

    await client.sleep_random(sleep_min, sleep_max)
    status, _ = await client.update_user_profile(username)
    if status!=200:
        raise RuntimeError("Failed to change user name")

    await client.sleep_random(sleep_min, sleep_max)
    await client.auth_logout()

    await client.sleep_random(sleep_min, sleep_max)
    status, _ = await client.login_with_username_and_password(username, password)
    if status!=200:
        raise RuntimeError("Failed to change user name")


async def run_new_user():
    client = PokerClient()
    async with client:
        await try_to_register(client)
    return client.user_id

async def main(count):
    tasks = [run_new_user() for _ in range(count)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    failed = 0
    for x in results:
        print(type(x), x)
        if not isinstance(x, int):
            failed += 1
    print(f"FAILURES: {failed}/{count}")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main(100))


