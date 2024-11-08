from decimal import Decimal

from ravvi_poker.engine.cards import Card
from ravvi_poker.engine.poker.bet import Bet
from ravvi_poker.engine.poker.player import Player


class SevenDeuceController:
    def __init__(self, seven_prize: int, big_blind: Decimal | int):
        # TODO округление
        self.each_prize_value: Decimal = Decimal(seven_prize * big_blind).quantize(Decimal(".01"))

    async def handle_winners(self, rounds_results: dict, players: list[Player]):
        bank_seven_deuce = 0
        winners_seven_deuce_user_id = []

        # обнуляем bet_delta у игроков
        for player in players:
            player.bet_delta = 0
            player.bet_amount = 0

        # собираем банк и победителей по seven deuce
        for board_results in rounds_results:
            bank_seven_deuce_delta, winners_seven_deuce_user_id_delta = \
                await self.collect_winners(board_results["rewards"], players)
            bank_seven_deuce += bank_seven_deuce_delta
            winners_seven_deuce_user_id.extend(winners_seven_deuce_user_id_delta)

        round_result = await self.form_result_and_balances(players, winners_seven_deuce_user_id,
                                                           bank_seven_deuce)

        return bank_seven_deuce, round_result

    async def collect_winners(self, winners_board: dict, players: list[Player]):
        bank_seven_deuce = 0
        winners_seven_deuce_user_id = []

        for player in [p for p in players if p.user_id in [w["user_id"] for w in winners_board["winners"]]]:
            player_cards = [Card(code=card) for card in player.cards]
            # если есть 7, 2 и они разномастные, то собираем в банк с других игроков деньги в банк seven deuce
            if 7 in (cards_ranks := [card.rank for card in player_cards]) and 2 in cards_ranks and \
                    player_cards[0].suit != player_cards[1].suit:
                winners_seven_deuce_user_id.append(player.user_id)

                for player_for_collect_sd in [p for p in players if p.user.id != player.user_id]:
                    if player_for_collect_sd.balance >= self.each_prize_value:
                        bank_seven_deuce += self.each_prize_value
                        player_for_collect_sd.bet_delta += self.each_prize_value
                        player_for_collect_sd.bet_amount += self.each_prize_value
                        player_for_collect_sd.bet_type = Bet.SEVEN_DEUCE
                        # TODO округление
                        player_for_collect_sd.user.balance = Decimal(player_for_collect_sd.user.balance -
                                                                     self.each_prize_value)
                    else:
                        bank_seven_deuce += player_for_collect_sd.user.balance
                        player_for_collect_sd.bet_delta += player_for_collect_sd.user.balance
                        player_for_collect_sd.bet_amount += player_for_collect_sd.user.balance
                        player_for_collect_sd.bet_type = Bet.SEVEN_DEUCE
                        player_for_collect_sd.user.balance = 0

        return bank_seven_deuce, winners_seven_deuce_user_id

    async def form_result_and_balances(self, players: list[Player], winners_seven_deuce_user_id: list,
                                       bank_seven_deuce: float) -> dict:
        winners = []
        rewards = {"type": "72", "winners": winners}
        round_result = {
            "rewards": rewards,
            "banks": [],
            "bank_total": 0
        }

        for player in players:
            if player.user_id in set(winners_seven_deuce_user_id):
                delta = Decimal(
                    bank_seven_deuce / len(winners_seven_deuce_user_id) *
                    winners_seven_deuce_user_id.count(player.user_id))
                # TODO округление
                player.user.balance = Decimal(player.user.balance + delta)
                winners.append(
                    {"user_id": player.user_id, "amount": delta, "balance": player.user.balance}
                )
        # TODO это можно перенести в модуль тестов
        winners.sort(key=lambda x: x["user_id"])

        return round_result
