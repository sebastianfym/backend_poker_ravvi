from .user import User


class Player:
    def __init__(self, user: User) -> None:
        self.user = user
        self.balance_0 = user.balance

    @property
    def user_id(self) -> int:
        return self.user.id

    @property
    def balance(self) -> int:
        return self.user.balance
