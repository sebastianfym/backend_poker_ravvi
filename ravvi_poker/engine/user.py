import asyncio
from decimal import Decimal
from typing import Set
from ..utils.timeout import TimeOut


class User:
    def __init__(self, id: int, name: str, image_id: int | None = None) -> None:
        self.id = id
        self.name = name
        self.image_id = image_id
        self.club_id = None
        self.account_id = None
        self.table_session_id = None
        self.balance: Decimal | None = None
        self.clients = set()
        self.inactive_timeout = None

        # timestamp в int
        self.buyin_offer_timeout: int | None = None
        # сумма отложенного пополнения баланса
        self.buyin_deferred: Decimal | None = None

        # флаг для новых игроков за столом (стоит в значении False ибо этот параметр важен только для RG и этот тип
        # стола сам им управляет)
        self.is_new_player_on_table: bool = False

    @property
    def connected(self) -> bool:
        return len(self.clients) > 0
    
    def add_client(self, client_id):
        self.clients.add(client_id)
        # сбрасывем таймер неактивности при подключении нового клиента
        self.clear_inactive()

    def remove_client(self, client_id):
        if client_id in self.clients:
            self.clients.remove(client_id)
        if not self.clients:
            self.set_inactive(60)

    @property
    def inactive(self) -> bool:
        return bool(self.inactive_timeout)

    def set_inactive(self, timeout: int):
        if self.inactive_timeout is None:
            self.inactive_timeout = TimeOut(timeout)

    def clear_inactive(self):
        self.inactive_timeout = None
        

    def get_info(self):
        return dict(
            id=self.id,
            name=self.name,
            image_id=self.image_id,
            balance=self.balance,
        )
