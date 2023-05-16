class Event(dict):
    
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
    GAME_ROUND = 302
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
    
    
    def __init__(self, type, **kwargs) -> None:
        super().__init__(type=type, **kwargs)

    @property
    def type(self):
        return self.get('type')
    
    def __getattr__(self, attr_name):
        return self.get(attr_name, None)
    

class TABLE_INFO(Event):
    def __init__(self, **kwargs) -> None:
        super().__init__(Event.TABLE_INFO, **kwargs)

class PLAYER_ENTER(Event):
    def __init__(self, **kwargs) -> None:
        super().__init__(Event.PLAYER_ENTER, **kwargs)

class PLAYER_EXIT(Event):
    def __init__(self, **kwargs) -> None:
        super().__init__(Event.PLAYER_EXIT, **kwargs)

class PLAYER_CARDS(Event):
    def __init__(self, **kwargs) -> None:
        super().__init__(Event.PLAYER_CARDS, **kwargs)

class PLAYER_BET(Event):
    def __init__(self, **kwargs) -> None:
        super().__init__(Event.PLAYER_BET, **kwargs)

class GAME_BEGIN(Event):
    def __init__(self, **kwargs) -> None:
        super().__init__(Event.GAME_BEGIN, **kwargs)

class GAME_ROUND(Event):
    def __init__(self, **kwargs) -> None:
        super().__init__(Event.GAME_ROUND, **kwargs)

class GAME_CARDS(Event):
    def __init__(self, **kwargs) -> None:
        super().__init__(Event.GAME_CARDS, **kwargs)

class GAME_PLAYER_MOVE(Event):
    def __init__(self, **kwargs) -> None:
        super().__init__(Event.GAME_PLAYER_MOVE, **kwargs)

class GAME_END(Event):
    def __init__(self, **kwargs) -> None:
        super().__init__(Event.GAME_END, **kwargs)
