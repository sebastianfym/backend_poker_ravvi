from random import randint

from ravvi_poker.engine.poker.bet import Bet


class BombPotController:
    def __init__(self, bombpot_settings: dict):
        self.double_board_mode: bool = bombpot_settings['double_board']
        self.freq: int = bombpot_settings["freq"]
        self.ante_min: int = bombpot_settings["ante_min"]
        self.ante_max: int = bombpot_settings["ante_max"]

        self.current_step: int = 1

    @property
    def is_bobmpot_active(self):
        return self.current_step == self.freq

    @property
    def bombpot_multiplier(self):
        return randint(self.ante_min, self.ante_max)

    async def handle_last_round(self):
        if self.current_step == self.freq:
            self.current_step = 1
        else:
            self.current_step += 1

    async def reset_step(self):
        self.current_step = 1


class BombPotMixin:
    async def run_PREFLOP(self):
        from ravvi_poker.engine.poker.base import Round
        from ravvi_poker.engine.poker.player import PlayerRole

        self.log.info("PREFLOP with BombPot begin")
        self.round = Round.PREFLOP

        self.players_to_role(PlayerRole.DEALER)
        self.players_rotate()
        for _ in range(self.PLAYER_CARDS_FREFLOP):
            for p in self.players:
                p.cards.append(self.deck.get_next())
        self.deck.get_next()

        async with self.DBI() as db:
            self.bet_level = 0

            for p in self.players:
                if p.user.balance <= self.blind_big * self.bombpot_blind_multiplier:
                    p.bet_type = Bet.ALLIN
                    p.bet_delta = p.user.balance
                    p.bet_amount = p.user.balance
                    p.bet_total += p.user.balance
                else:
                    p.bet_type = Bet.BOMBPOT_ANTE
                    p.bet_delta = self.blind_big * self.bombpot_blind_multiplier
                    p.bet_amount = self.blind_big * self.bombpot_blind_multiplier
                    p.bet_total += self.blind_big * self.bombpot_blind_multiplier
                self.bank_total = round(self.bank_total + p.bet_delta, 2)
                p.user.balance -= p.bet_delta
                await self.broadcast_PLAYER_BET(db, p)

            for p in self.players:
                p.hand = self.get_best_hand(p.cards, self.cards)
                await self.broadcast_PLAYER_CARDS(db, p)

        self.update_status()

        self.log.info("PREFLOP with BombPot end")
