from dataclasses import dataclass, asdict

@dataclass
class User:
    id: int
    username: str
    balance: int
    connected: int = 0
