from dataclasses import dataclass, asdict

@dataclass
class User:
    id: int
    username: str
    image_id: int
    balance: int
    connected: int = 0
