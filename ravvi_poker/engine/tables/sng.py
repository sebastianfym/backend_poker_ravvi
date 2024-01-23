import asyncio
import contextlib
from .base import Table
from .status import TableStatus
from ..time import TimeCounter, timedelta
from ..info import sng_standard, sng_turbo
from ...db import DBI

class Table_SNG(Table):
    
    TABLE_TYPE = "SNG"

    def __init__(self, id, **kwargs):
        super().__init__(id, **kwargs)
        self.time_counter = TimeCounter()
        # текущий уровень
        self.level_current_idx = -1
        self.level_current = None
        # следующий уровень
        self.level_next = None
        #  время смены уровня
        self.level_end = None

    def parse_props(self, 
                    buyin_value=10000, buyin_cost=0,
                    level_schedule="STANDARD", level_time=2,
                    **kwargs):
        self.buyin_value = buyin_value
        self.buyin_cost = buyin_cost
        self.level_schedule = level_schedule
        if self.level_schedule=="STANDARD":
            self.levels = sng_standard
        elif self.level_schedule=="TURBO":
            self.levels = sng_turbo
        else:
            self.level_schedule = "STANDARD"
            self.levels = sng_standard
        self.level_time = level_time

    @property
    def user_enter_enabled(self):
        return self.time_counter.total_seconds == 0

    @property
    def user_exit_enabled(self):
        return self.time_counter.total_seconds == 0

    async def run_levels(self):
        while True:
            await self.sleep(1)
            total_seconds = self.time_counter.total_seconds
            level_seconds = self.level_time * 60
            idx = min(int(self.time_counter.total_seconds / level_seconds), len(self.levels) - 1)
            if idx == self.level_current_idx:
                # пока ничего не изменилось
                continue
            # смена уровня
            self.level_current_idx = idx
            self.level_current = self.levels[idx]
            next_idx = idx + 1            
            if next_idx < len(self.levels):
                # обновляем информацию о новом следующем уровне
                self.level_next = self.levels[next_idx]
                now = self.time_counter._now()
                reminder = level_seconds - total_seconds % level_seconds
                self.level_end = now + timedelta(seconds=reminder)
            else:
                # следующего уровня больше нет
                reminder = None
                self.level_next = None
                self.level_end = None

            async with self.DBI() as db:
                self.broadcast_TABLE_NEXT_LEVEL_INFO(
                    db, 
                    seconds = reminder, 
                    blind_small = self.level_next.blind_small if self.level_next else None, 
                    blind_big = self.level_next.blind_big if self.level_next else None,
                    ante = self.level_next.ante if self.level_next else None
                )

    async def run_table(self):
        # wait for players take all seats available
        while self.status == TableStatus.OPEN:
            if all(self.seats):
                break
            await self.sleep(1)

        # фиксируем время начала турнира
        self.time_counter.start()

        # запускаем обновление уровней
        task2 = asyncio.create_task(self.run_levels())

        # основной цикл
        while self.status == TableStatus.OPEN:
            await self.sleep(self.NEW_GAME_DELAY)
            await self.run_game()
            async with self.lock:
                async with self.DBI() as db:
                    await self.remove_users(db)
                users = [u for u in self.seats if u]
                if len(users)<2:
                    self.status = TableStatus.CLOSING

        # останавливаем обновлятор уровней
        if not task2.done():
            task2.cancel()
        with contextlib.suppress(asyncio.exceptions.CancelledError):
            await task2
        

            
