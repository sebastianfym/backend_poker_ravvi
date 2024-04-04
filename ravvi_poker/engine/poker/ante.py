from decimal import Decimal

from ravvi_poker.engine.poker.base import Round


class AnteUpController:
    def __init__(self, blind_small_value: int | Decimal):
        self.ante_levels = self.get_ante_levels(blind_small_value)
        self.current_ante_value: Decimal | int | None = None if len(self.ante_levels) == 0 else self.ante_levels[0]

    def get_ante_levels(self, blind_small_value: int | Decimal) -> list[int | Decimal]:
        if blind_small_value == Decimal("0.01"):
            return []
        if blind_small_value == Decimal("0.02"):
            return [Decimal("0.01"), Decimal("0.02")]
        elif blind_small_value in [Decimal("0.03"), Decimal("0.04")]:
            return [Decimal("0.01"), Decimal("0.02"), Decimal("0.03")]
        else:
            return [Decimal(blind_small_value * 2 * multiplier).quantize(Decimal(".01")) for multiplier in
                    [Decimal("0.2"), Decimal("0.3"), Decimal("0.4"), Decimal("0.5")]]

    async def handle_last_round_type(self, last_round_type: Round):
        # обрабатывает результаты игры для того, чтобы определить следующее значение анте
        if self.current_ante_value is not None:
            # если на последнем, то смотрим чем закончилась раздача. Если вскрытием, то меняем значение анте на самое
            # малое
            if last_round_type is Round.SHOWDOWN:
                self.current_ante_value = self.ante_levels[0]
            elif self.current_ante_value != self.ante_levels[-1]:
                self.current_ante_value = self.ante_levels[self.ante_levels.index(self.current_ante_value) + 1]

    async def reset_ante_level(self):
        if self.current_ante_value != self.ante_levels[0]:
            self.current_ante_value = self.ante_levels[0] if len(self.ante_levels) != 0 else None
