from dataclasses import dataclass, asdict

@dataclass
class User:
    user_id: int
    username: str
    balance: int
    connected: int = 0

    def asdict(self):
        return asdict(self)