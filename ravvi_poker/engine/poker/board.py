from enum import unique, Enum


@unique
class BoardType(Enum):
    BOARD1 = "board1"
    BOARD2 = "board2"
    BOARD3 = "board3"


class Board:
    def __init__(self, board_type: BoardType):
        self.board_type = board_type
        self.cards: list = []

    def append_card(self, card: int):
        self.cards.append(card)
