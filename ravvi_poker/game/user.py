from dataclasses import dataclass, asdict

@dataclass
class User:
    id: int
    username: str
    image_id: int|None = None
    balance: int = 0
    connected: int = 0
