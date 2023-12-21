from typing import Set


class User:
    def __init__(self, id:int, name:str, image_id=int|None) -> None:
        self.id = id
        self.name = name
        self.image_id = image_id
        self.club_id = None
        self.account_id = None
        self.balance = None
        self.clients = set()

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
