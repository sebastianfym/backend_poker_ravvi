from dataclasses import dataclass, asdict

@dataclass
class User:
    user_id: int
    username: str
    balance: int

    def asdict(self):
        return asdict(self)