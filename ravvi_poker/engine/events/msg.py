from enum import IntEnum, unique

@unique
class MessageType(IntEnum):
    
    TABLE_INFO = 101
    TABLE_ERROR = 102
    TABLE_NEXT_LEVEL_INFO = 110
    TABLE_CLOSED = 199

    PLAYER_ENTER = 201
    PLAYER_SEAT = 202
    PLAYER_CARDS = 203
    PLAYER_BET = 204
    PLAYER_EXIT = 299

    GAME_BEGIN = 301
    GAME_ROUND = 302
    GAME_CARDS = 303
    GAME_PLAYER_MOVE  = 304
    GAME_RESULT = 390
    GAME_END = 399

    @classmethod
    def verify(cls, value):
        return value in cls._value2member_map_
    
    @classmethod
    def decode(cls, x):
        if isinstance(x, str):
            return cls.__members__[x]
        return cls._value2member_map_[x]


class Message(dict):
    
    Type = MessageType

    def __init__(self, id=None, *, msg_type:int, table_id:int=None, game_id:int=None, cmd_id=None, client_id=None, **props) -> None:
        super().__init__(table_id=table_id, game_id=game_id, msg_type=msg_type, cmd_id=cmd_id, client_id=client_id, props=props)
        self.id = id


    @property
    def table_id(self):
        return self.get('table_id')

    @property
    def game_id(self):
        return self.get('game_id')
    
    @property
    def msg_type(self):
        return self.get('msg_type')
    
    @property
    def cmd_id(self):
        return self.get('cmd_id')
    
    @property
    def client_id(self):
        return self.get('client_id')

    @property
    def props(self):
        return self.get('props')

    def __getattr__(self, attr_name):
        return self.props.get(attr_name, None)
