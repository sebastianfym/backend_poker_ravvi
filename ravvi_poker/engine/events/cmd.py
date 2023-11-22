from enum import IntEnum, unique

@unique
class CommandType(IntEnum):
    JOIN = 11
    EXIT = 12
    TAKE_SEAT = 13
    
    BET = 21

    @classmethod
    def verify(cls, value):
        return value in cls._value2member_map_
    
    @classmethod
    def decode(cls, x):
        if isinstance(x, str):
            return cls.__members__[x]
        return cls._value2member_map_[x]


class Command(dict):
    
    Type = CommandType

    def __init__(self, id=None, *, table_id:int, cmd_type:CommandType, client_id:int, **props) -> None:
        super().__init__(client_id=client_id, table_id=table_id, cmd_type=cmd_type, props=props)
        self.id = id

    @property
    def client_id(self):
        return self.get('client_id')

    @property
    def table_id(self):
        return self.get('table_id')

    @property
    def cmd_type(self):
        return self.get('cmd_type')
    
    @property
    def props(self):
        return self.get('props')

    def __getattr__(self, attr_name):
        return self.props.get(attr_name, None)
