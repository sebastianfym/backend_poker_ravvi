from typing import List
from itertools import groupby
from .player import Player

def get_banks(players: List[Player]):
    players = list(players)
    players.sort(key=lambda x: x.bet_total)
    levels = []
    for l, g in groupby(players, key=lambda x: x.bet_total):
        g = list(g)
        levels.append((l,g))
    levels.reverse()
    for i in range(len(levels)-1):
        _, g = levels[i]
        _, p = levels[i+1]
        p.extend(g)
    levels.reverse()
    banks = []
    level = 0
    for l, group in levels:
        amount = (l-level)*len(group)
        group = [p for p in group if p.in_the_game]
        banks.append((amount, group))
        level = l
    for i, (amount, group) in enumerate(banks):
        if i==0:
            continue
        p_amount, p_group = banks[i-1]
        p_ids = set(p.user_id for p in p_group)
        ids = set(p.user_id for p in group)
        if not p_ids or p_ids==ids:
            banks[i-1] = None
            banks[i] = (p_amount+amount, group)
    banks = [b for b in banks if b]
    total = sum([b[0] for b in banks])
    return banks, total
