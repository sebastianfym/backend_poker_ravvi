from ravvi_poker.client.cards_set import one_suit, multi_suit
from ravvi_poker.engine.cards import Card


def card_decoder(msg):
    cards_code = msg.props['hands'][0]['hand_cards']
    one_suit_check = True

    card1 = list(str(Card(code=cards_code[0])))
    card2 = list(str(Card(code=cards_code[1])))
    combo = card1[0] + card2[0]

    if card1[1] != card2[1]:
        one_suit_check = False

    list_with_combo = multi_suit
    if one_suit_check:
        list_with_combo = one_suit

    if combo in list_with_combo:
        print('КОМБИНАЦИЯ ДОСТУПНА')
        return True
    else:
        print('КОМБИНАЦИЯ НЕ ДОСТУПНА')
        return False
