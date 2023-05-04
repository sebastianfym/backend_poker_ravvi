class User:
    def __init__(self, user_id) -> None:
        self.user_id = user_id
    
    def __str__(self) -> str:
        return f"User({self.user_id})"
    
    def __repr__(self) -> str:
        return f"User({self.user_id})"

    
class Table:

    def __init__(self, n_seats=9):
        self.table_id = None
        self.seats = [None]*n_seats
        self.dealer_idx = -1

    def get_players(self, min_size):
        players = [(i, p) for i, p in enumerate(self.seats) if p is not None]
        if len(players)<min_size:
            return None
        max_idx = players[-1][0]
        self.dealer_idx += 1
        if self.dealer_idx>max_idx:
            self.dealer_idx = 0
        while players[0][0]<self.dealer_idx:
            p = players.pop(0)
            players.append(p)
        self.dealer_idx = players[0][0]
        return [p for i, p in players]

