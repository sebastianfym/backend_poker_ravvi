from ravvi_poker.engine.poker.base import Round


class AnteUpController:
    def __init__(self, blind_small_value: float):
        self.ante_levels = self.get_ante_levels(blind_small_value)
        self.current_ante_value: float | None = None if len(self.ante_levels) == 0 else self.ante_levels[0]

    def get_ante_levels(self, blind_small_value: float) -> list[float]:
        if blind_small_value == 0.01:
            return []
        if blind_small_value == 0.02:
            return [0.01, 0.02]
        elif blind_small_value in [0.03, 0.04]:
            return [0.01, 0.02, 0.03]
        else:
            # TODO округление
            return [round(blind_small_value * 2 * multiplier, 2) for multiplier in
                    [0.2, 0.3, 0.4, 0.5]]

    async def handle_last_round_type(self, last_round_type: Round):
        # обрабатывает результаты игры для того, чтобы определить следующее значение анте
        if self.current_ante_value is not None:
            # если на последнем, то смотрим чем закончилась раздача. Если вскрытием, то меняем значение анте на самое
            # малое
            if last_round_type is Round.SHOWDOWN:
                self.current_ante_value = self.ante_levels[0]
            elif self.current_ante_value != self.ante_levels[-1]:
                self.current_ante_value = self.ante_levels[self.ante_levels.index(self.current_ante_value) + 1]
