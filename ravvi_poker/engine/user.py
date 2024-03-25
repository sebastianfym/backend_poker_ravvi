import asyncio
from decimal import Decimal
from typing import Set


class User:
    def __init__(self, id:int, name:str, image_id: int|None = None) -> None:
        self.id = id
        self.name = name
        self.image_id = image_id
        self.club_id = None
        self.account_id = None
        self.table_session_id = None
        self.balance = None
        self.clients = set()

        self.buyin_offer_timeout: int | None = None
        self.buyin_deferred_value: Decimal | None = None

    @property
    def connected(self) -> bool:
        return len(self.clients) > 0

    def get_info(self):
        return dict(
            id=self.id,
            name=self.name,
            image_id=self.image_id,
            balance=self.balance,
        )
