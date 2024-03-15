import asyncio
import psycopg
from collections import deque

class DBIPool:
    def __init__(self, conninfo, limit=5, cache_limit=None) -> None:
        self.conninfo = conninfo
        self.lock = asyncio.Semaphore(limit)
        self.cache_limit = min(limit, cache_limit or int(limit/2))
        self.cache = deque()

    async def open(self):
        pass

    async def close(self):
        while self.cache:
            dbi = self.cache.pop()
            await dbi.close()

    async def getconn(self):
        await self.lock.acquire()
        if self.cache:
            dbi = self.cache.pop()
        else:
            dbi = await psycopg.AsyncConnection.connect(self.conninfo)
        return dbi

    async def putconn(self, dbi, exc_type):
        if exc_type:
            await dbi.close()
        else:
            self.cache.append(dbi)
            if len(self.cache)>self.cache_limit:
                dbi = self.cache.popleft()
                await dbi.close()
        self.lock.release()
