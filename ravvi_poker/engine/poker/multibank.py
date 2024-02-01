from logging import getLogger
from typing import List
from itertools import groupby
from .player import Player

logger = getLogger(__name__)


def get_banks(players: List[Player]):
    logger.debug("Staring form banks")
    players = list(players)
    logger.debug("Players: \n" + "\n".join([str(p) for p in players]))
    players.sort(key=lambda x: x.bet_total)

    logger.debug("Form levels")
    levels = []
    for l, g in groupby(players, key=lambda x: x.bet_total):
        g = list(g)
        levels.append((l, g))
    levels.reverse()
    logger.debug("Levels: \n" + "\n".join([f"{level}" for level in levels]))

    logger.debug("Polulate lower levels with upper players")
    for i in range(len(levels) - 1):
        _, g = levels[i]
        _, p = levels[i + 1]
        p.extend(g)
        logger.debug(f"Populate level {levels[i]} with players: \n" + "\n".join([str(player) for player in g]))
    levels.reverse()
    logger.debug("Result of populate: \n" + "\n".join([f"{level}" for level in levels]))

    logger.debug("Form banks from levels")
    banks = []
    level = 0
    for l, group in levels:
        amount = (l - level) * len(group)
        group = [p for p in group if p.in_the_game]
        banks.append((amount, group))
        level = l
    logger.debug("Result of form banks: \n" + "\n".join([f"{bank}" for bank in banks]))

    for i, (amount, group) in enumerate(banks):
        if i == 0:
            continue
        p_amount, p_group = banks[i - 1]
        p_ids = set(p.user_id for p in p_group)
        ids = set(p.user_id for p in group)
        if not p_ids or p_ids == ids:
            banks[i - 1] = None
            banks[i] = (p_amount + amount, group)

    banks = [b for b in banks if b]
    total = sum([b[0] for b in banks])
    logger.debug(f"Total: {total}")
    return banks, total
