from enum import IntEnum, unique

@unique
class Bet(IntEnum):    
    FOLD = 1
    SMALL_BLIND = 11
    BIG_BLIND = 12
    CALL = 21
    CHECK = 22
    RAISE = 30
    ALLIN = 99

    @classmethod
    def verify(cls, value):
        return value in cls._value2member_map_
    
    @classmethod
    def decode(cls, x):
        if isinstance(x, str):
            return cls.__members__[x]
        return cls._value2member_map_[x]


