from typing import Set


class User:
    def __init__(self, id, username=None, image_id=None) -> None:
        self.id = id
        self.username = username or f"u{id}"
        self.image_id = None
        self.balance = None
        self.clients = set()

    @property
    def connected(self):
        return len(self.clients) > 0

    def get_info(self):
        return dict(
            user_id=self.id,
            username=self.username,
            image_id=self.image_id,
            balance=self.balance,
        )
