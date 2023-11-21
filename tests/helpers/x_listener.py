import asyncio

from ravvi_poker.db.listener import DBI, Notify, DBI_Listener

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
