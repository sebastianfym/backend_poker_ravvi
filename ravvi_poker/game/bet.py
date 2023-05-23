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
