from enum import Enum, unique, IntEnum


@unique
class TableStatus(IntEnum):
    STOPPED = 0
    STARTUP = 1
    REGISTER = 2
    OPEN = 5
    SHUTDOWN = 7
    CLOSING = 8
    CLOSED = 9
