from ravvi_poker.engine.cards import Card
from ravvi_poker.engine.poker.hands import Hand
from ravvi_poker.engine.poker.player import Player


class SevenDeuceController:
    def __init__(self, seven_prize: int):
        self.each_prize: int = seven_prize

    async def handle_winners(self, winners_info: dict, players: list[Player]):
        bank_seven_deuce = 0
        winners_seven_deuce_user_id = []

        # обнуляем bet_delta у игроков
        for player in players:
            player.bet_delta = 0

        # собираем банк и победителей по seven deuce
        for winners_board in winners_info:
            bank_seven_deuce_delta, winners_seven_deuce_user_id_delta = \
                await self.collect_winners(winners_board, players)
            bank_seven_deuce += bank_seven_deuce_delta
            winners_seven_deuce_user_id.extend(winners_seven_deuce_user_id_delta)

        rewards, balances = await self.form_rewards_and_balances(players, winners_seven_deuce_user_id, bank_seven_deuce)
        # TODO это можно перенести в модуль тестов
        balances.sort(key=lambda x: x["user_id"])
        [rewards_list["winners"].sort(key=lambda x: x["user_id"]) for rewards_list in rewards]

        return bank_seven_deuce, rewards, balances

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
                    if player_for_collect_sd.balance >= self.each_prize:
                        bank_seven_deuce += self.each_prize
                        player_for_collect_sd.bet_delta += self.each_prize
                        # TODO округление
                        player_for_collect_sd.user.balance = round(player_for_collect_sd.user.balance -
                                                                   self.each_prize, 2)
                    else:
                        bank_seven_deuce += player_for_collect_sd.user.balance
                        player_for_collect_sd.bet_delta += player_for_collect_sd.user.balance
                        player_for_collect_sd.user.balance = 0

        return bank_seven_deuce, winners_seven_deuce_user_id

    async def form_rewards_and_balances(self, players: list[Player], winners_seven_deuce_user_id: list,
                                        bank_seven_deuce: float):
        winners = []
        rewards = [
            {"type": "seven_deuce", "winners": winners}
        ]
        balances = []

        for player in players:
            if player.user_id in set(winners_seven_deuce_user_id):
                delta = round(
                    bank_seven_deuce / len(winners_seven_deuce_user_id) *
                    winners_seven_deuce_user_id.count(player.user_id), 2)
                # TODO округление
                player.user.balance = round(player.user.balance + delta, 2)
                winners.append(
                    {"user_id": player.user_id, "amount": delta}
                )
                balances.append({
                    "user_id": player.user_id,
                    "balance": player.user.balance,
                    "delta": delta - player.bet_delta
                })
            else:
                balances.append({
                    "user_id": player.user_id,
                    "balance": player.user.balance,
                    "delta": player.bet_delta * (-1)
                })

        return rewards, balances
