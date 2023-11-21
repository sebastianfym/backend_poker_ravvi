import asyncio
import pytest
import pytest_asyncio
from ravvi_poker.db.adbi import DBI, Notify
from ravvi_poker.db.listener import DBI_Listener


@pytest.mark.asyncio
async def test_01_user_client_closed(client):
    assert client.id
    async with X_DBI_Listener("user_client_closed") as x:
        async with DBI() as db:
            row = await db.close_client(client.id)
            assert row
            assert row.closed_ts
    assert x.expected and len(x.expected) == 1
    payload = x.expected[0]
    assert payload["client_id"] == client.id


class X_DBI_Listener(DBI_Listener):
    def __init__(self, channel, sleep=1) -> None:
        super().__init__()
        self.channels = {channel: self.on_expected}
        self.expected = []
        self.other = []
        self._sleep = sleep

    async def on_expected(self, db: DBI, **payload):
        # print(payload)
        self.expected.append(payload)

    async def on_notify_default(self, db: DBI, msg: Notify):
        # print(msg)
        self.other.append(msg)

    async def __aenter__(self):
        self.expected = []
        self.other = []
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_value, exc_tb):
        await asyncio.sleep(self._sleep)
        await self.stop()


async def main():
    await DBI.pool_open()
    async with X_DBI_Listener("user_client_closed") as x:
        await asyncio.sleep(30)
    await DBI.pool_close()


if __name__ == "__main__":
    asyncio.run(main())
