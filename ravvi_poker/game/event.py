
class Event(dict):
    
    CMD_TABLE_JOIN  = 11
    CMD_TABLE_LEAVE = 12
    CMD_TAKE_SEAT = 13
    CMD_PLAYER_BET  = 21

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
        return None
    
    @classmethod
    def from_row(cls, row):
        props = row.event_props
        props['table_id'] = row.table_id
        for k in ['game_id','user_id']:
            v = getattr(row, k, None) 
            if v:
                props[k] = v
        return Event(row.event_type, **props)
        
    def __init__(self, type, **kwargs) -> None:
        super().__init__(type=type, **kwargs)

    def clone(self):
        return Event(**self)

    @property
    def type(self):
        return self.get('type')
    
    def __getattr__(self, attr_name):
        return self.get(attr_name, None)
    

def CMD_TABLE_JOIN(*, table_id, take_seat):
    return Event(Event.CMD_TABLE_JOIN, table_id=table_id, take_seat=take_seat)

def CMD_PLAYER_BET(*, table_id, bet, amount=None):
    return Event(Event.CMD_PLAYER_BET, table_id=table_id, bet=bet, amount=amount)

def TABLE_INFO(**kwargs):
    return Event(Event.TABLE_INFO, **kwargs)

def TABLE_ERROR(table_id, **kwargs):
    return Event(Event.TABLE_ERROR, table_id=table_id, **kwargs)

def TABLE_NEXT_LEVEL_INFO(table_id, **kwargs):
    return Event(Event.TABLE_NEXT_LEVEL_INFO, table_id=table_id, **kwargs)

def TABLE_CLOSED(**kwargs):
    return Event(Event.TABLE_CLOSED, **kwargs)

def PLAYER_ENTER(**kwargs):
    return Event(Event.PLAYER_ENTER, **kwargs)

def PLAYER_EXIT(**kwargs):
    return Event(Event.PLAYER_EXIT, **kwargs)

def PLAYER_CARDS(**kwargs):
    return Event(Event.PLAYER_CARDS, **kwargs)

def PLAYER_BET(**kwargs):
    return Event(Event.PLAYER_BET, **kwargs)

def GAME_BEGIN(**kwargs):
    return Event(Event.GAME_BEGIN, **kwargs)

def GAME_ROUND(**kwargs):
    return Event(Event.GAME_ROUND, **kwargs)

def GAME_CARDS(**kwargs):
    return Event(Event.GAME_CARDS, **kwargs)

def GAME_PLAYER_MOVE(**kwargs):
    return Event(Event.GAME_PLAYER_MOVE, **kwargs)

def GAME_RESULT(**kwargs):
    return Event(Event.GAME_RESULT, **kwargs)

def GAME_END(**kwargs):
    return Event(Event.GAME_END, **kwargs)
