from .user import User


class Player:
    def __init__(self, user: User) -> None:
        self.user = user
        self.balance_0 = user.balance
        self.cards = None
        self.cards_open = False

        self.cards_open_on_request: list | None = None

    @property
    def id(self) -> int:
        return self.user.id

    @property
    def user_id(self) -> int:
        return self.user.id

    @property
    def balance(self) -> int:
        return self.user.balance

    def __str__(self):
        return (f"Player: {self.user_id} - {self.user.name}\n"
                f"Role: {self.role}\n"
                f"BetType: {self.bet_type}\n"
                f"BetAmount: {self.bet_amount}\n"
                f"BetAnte: {self.bet_ante}\n"
                f"BetTotal: {self.bet_total}")
