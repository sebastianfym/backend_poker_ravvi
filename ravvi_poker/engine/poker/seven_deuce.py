from ravvi_poker.engine.cards import Card
from ravvi_poker.engine.poker.hands import Hand
from ravvi_poker.engine.poker.player import Player


class SevenDeuceController:
    def __init__(self, seven_prize: int):
        self.each_prize: int = seven_prize

    async def handle_winners(self, winners_info: dict, players: list[Player]):
        bank_seven_deuce = 0
        winners_seven_deuce_user_id = []

        # собираем банк и победителей по seven deuce
        if isinstance(winners_info[0], list):
            # winners для double board
            for num, winners_board in enumerate(winners_info):
                bank_seven_deuce_delta, winners_seven_deuce_user_id_delta = \
                    await self.handle_winners(winners_info[num], players)
                bank_seven_deuce += bank_seven_deuce_delta
                winners_seven_deuce_user_id.append(winners_seven_deuce_user_id_delta)
        else:
            # winners для любого другого режима
            for player in [p for p in players if p.user_id in [w["user_id"] for w in winners_info]]:
                # TODO если рука закрыта, то нужно ли ее открыть?

                winners_seven_deuce_user_id.append(player.user_id)

                player_cards = [Card(code=card) for card in player.cards]
                # если есть 7, 2 и они разномастные, то собираем в банк с других игроков деньги в банк seven deuce
                if 7 in (cards_ranks := [card.rank for card in player_cards]) and 2 in cards_ranks and \
                        player_cards[0].suit != player_cards[1].suit:
                    for player_for_collect_sd in [p for p in players if p.user.id != player.user_id]:
                        if player_for_collect_sd.balance >= self.each_prize:
                            bank_seven_deuce += self.each_prize
                            # TODO дельта нужна?
                            player_for_collect_sd.user.balance -= self.each_prize
                        else:
                            bank_seven_deuce += player_for_collect_sd.user.balance
                            player_for_collect_sd.user.balance = 0

        winners_info = []
        for player_user_id in winners_seven_deuce_user_id:
            for player in players:
                if player_user_id == player.user_id:
                    delta = round(bank_seven_deuce / len(winners_seven_deuce_user_id), 2)
                    # TODO дельта нужна?
                    player.user.balance += delta

                    if player_user_id not in [w["user_id"] for w in winners_info]:
                        winners_info.append({
                            "user_id": player_user_id,
                            "balance": player.user.balance,
                            "delta": delta
                        })
                    else:
                        for num, winner in enumerate(winners_info):
                            if winner["user_id"] == player_user_id:
                                winners_info[num] = {
                                    "user_id": player_user_id,
                                    "balance": player.user.balance,
                                    "delta": delta + winner["delta"]
                                }

        return bank_seven_deuce, winners_info
