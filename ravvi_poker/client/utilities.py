from ravvi_poker.client.cards_set import one_suit, multi_suit
from ravvi_poker.engine.cards import Card
from ravvi_poker.engine.events import CommandType


def card_decoder(msg): #  На первый ход на стол кладется 3 карты, так вот сделать проверку (если в msg карты 3, то это на стол)
    cards_code = msg.props['hands'][0]['hand_cards']

    if len(cards_code) > 2:
        if msg.props['hands'][0]['hand_type'] != "H":
            # print(f'меняю старшие карты на пару')
            return [None, True]
        return None

    one_suit_check = True
    card1 = list(str(Card(code=cards_code[0])))
    card2 = list(str(Card(code=cards_code[1])))
    print(card1, card2) # этот принт служил для просмотра карт в руке бота
    combo = card1[0] + card2[0]

    if card1[1] != card2[1]:
        one_suit_check = False

    list_with_combo = multi_suit
    if one_suit_check:
        list_with_combo = one_suit

    if combo in list_with_combo:
        print(f'КОМБИНАЦИЯ ДОСТУПНА {msg["props"]["hands"][0]["hand_type"]}')
        return True
    else:
        print(f'КОМБИНАЦИЯ НЕ ДОСТУПНА {msg["props"]["hands"][0]["hand_type"]}')
        return False

