from ravvi_poker.engine.poker.base import PokerBase


class Poker_OFC_X(PokerBase):
    GAME_TYPE = "OFC"


class Poker_OFC_Regular(PokerBase):
    GAME_SUBTYPE = "REGULAR"


class Poker_OFC_Advanced(PokerBase):
    GAME_SUBTYPE = "ADVANCED"


class Poker_OFC_Limited(PokerBase):
    GAME_SUBTYPE = "LIMITED"


OFC_GAMES = [
    Poker_OFC_Regular,
    Poker_OFC_Advanced,
    Poker_OFC_Limited
]
