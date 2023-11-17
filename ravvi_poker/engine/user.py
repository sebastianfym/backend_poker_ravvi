from typing import Set
from dataclasses import dataclass, field


@dataclass
class User:
    id: int
    username: str
    image_id: int | None = None
    balance: int = 0
    clients: Set[int] = field(default_factory=set)

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
