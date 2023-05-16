class Events(dict):
    
    CMD_TABLE_JOIN  = 11
    CMD_TABLE_LEAVE = 12
    CMD_PLAYER_BET  = 21

    TABLE_INFO = 101

    PLAYER_ENTER = 201
    PLAYER_SEAT = 202
    PLAYER_CARDS = 203
    PLAYER_BET = 204
    PLAYER_EXIT = 299

    GAME_BEGIN = 301
    GAME_BANK = 302
    GAME_CARDS = 303
    GAME_PLAYER_MOVE  = 304
    GAME_END = 399

    @classmethod
    def iter_events(cls):
        for k, v in cls.__dict__.items():
            if k[0]=='_' or not isinstance(v, int):
                continue
            yield k, v

    @classmethod
    def name(cls, code):
        for k, v in cls.iter_events():
            if v==code:
                return k
        return '???'
    
    def __init__(self, type) -> None:
        super()