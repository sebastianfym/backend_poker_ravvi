from ..client import PokerClient

async def try_register(client: PokerClient, *,  sleep_min = 2, sleep_max = 5):
    """Регистрация пользователя с несколькими попытками и настройка профиля"""
    for _ in range(1):
        await  client.sleep_random(sleep_min, sleep_max)
        status, _ = await client.auth_register()
        if status==200:
            break
    if status!=200:
        raise RuntimeError("Failed to register user", status)


async def try_set_username_and_password(client: PokerClient, username, password, *,  sleep_min = 2, sleep_max = 5):
    await client.sleep_random(sleep_min, sleep_max)
    status, _ = await client.password_update("", password)
    if status!=200:
        raise RuntimeError("Failed to set password")
    await client.sleep_random(sleep_min, sleep_max)
    status, payload = await client.update_user_profile(username)
    if status!=200:
        #print(payload)
        raise RuntimeError("Failed to change username")
